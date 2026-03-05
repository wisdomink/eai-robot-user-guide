"""
FF Master RAG Evaluation Script

Sends test questions to the OpenAI Assistants API (same pipeline as the
RAG service), collects streaming responses, then uses GPT to score each
answer against the expected reference.

Usage:
    cd rag_server
    python -m eval.run_eval                       # run all test cases
    python -m eval.run_eval --ids 1 2 3           # run specific cases
    python -m eval.run_eval --category safety      # run by category
    python -m eval.run_eval --report results.json  # custom output path
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from openai import AsyncOpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_ASSISTANT_ID

EVAL_DIR = Path(__file__).resolve().parent
TEST_CASES_PATH = EVAL_DIR / "test_cases.json"
DEFAULT_REPORT_PATH = EVAL_DIR / "report.json"

JUDGE_MODEL = "gpt-4o"

oai = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ── Scoring prompt ────────────────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT = """\
You are an expert evaluator for a RAG (Retrieval-Augmented Generation) system \
that answers questions about the FF Master humanoid robot user manual.

You will receive:
- **Question**: the user's question
- **Expected Answer**: the ground-truth reference answer
- **Actual Answer**: the RAG system's response

Score the Actual Answer on three dimensions (each 0-10):

1. **Accuracy** (0-10): Are the facts in the actual answer correct compared \
to the expected answer? Deduct points for wrong numbers, incorrect procedures, \
or factual errors.
2. **Completeness** (0-10): Does the actual answer cover all key points in \
the expected answer? Deduct points for missing important information.
3. **Relevance** (0-10): Is the actual answer focused and free of irrelevant \
or misleading information? Deduct points for off-topic content.

Respond with ONLY valid JSON (no markdown fences) in this exact format:
{
  "accuracy": <0-10>,
  "completeness": <0-10>,
  "relevance": <0-10>,
  "overall": <0-10>,
  "comment": "<brief explanation in Chinese, 1-3 sentences>"
}

The "overall" score should be a weighted average: \
accuracy×0.4 + completeness×0.35 + relevance×0.25, rounded to 1 decimal.\
"""


# ── Query the RAG assistant (streaming) ───────────────────────────────────

async def ask_assistant(question: str) -> str:
    """Send a question to the Assistants API and collect the full streamed response."""
    thread = await oai.beta.threads.create()
    await oai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question,
    )

    full_text = ""
    async with oai.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=OPENAI_ASSISTANT_ID,
    ) as stream:
        async for event in stream:
            if event.event == "thread.message.delta":
                for part in event.data.delta.content or []:
                    if hasattr(part, "text") and part.text:
                        full_text += part.text.value or ""

    # clean up the thread
    try:
        await oai.beta.threads.delete(thread.id)
    except Exception:
        pass

    return full_text.strip()


# ── Judge with GPT ────────────────────────────────────────────────────────

async def judge_answer(
    question: str, expected: str, actual: str
) -> dict:
    """Use GPT to score the actual answer against the expected answer."""
    user_content = (
        f"**Question**: {question}\n\n"
        f"**Expected Answer**: {expected}\n\n"
        f"**Actual Answer**: {actual}"
    )

    resp = await oai.chat.completions.create(
        model=JUDGE_MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
    )

    raw = resp.choices[0].message.content or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "accuracy": 0,
            "completeness": 0,
            "relevance": 0,
            "overall": 0,
            "comment": f"Failed to parse judge response: {raw[:200]}",
        }


# ── Run a single test case ────────────────────────────────────────────────

async def run_single(case: dict, index: int, total: int) -> dict:
    cid = case["id"]
    question = case["question"]
    expected = case["expected_answer"]

    print(f"\n[{index}/{total}] Case #{cid}: {question[:60]}...")

    t0 = time.time()
    actual_answer = await ask_assistant(question)
    query_time = round(time.time() - t0, 2)
    print(f"  ↳ RAG responded in {query_time}s ({len(actual_answer)} chars)")

    t1 = time.time()
    scores = await judge_answer(question, expected, actual_answer)
    judge_time = round(time.time() - t1, 2)

    overall = scores.get("overall", 0)
    status = "✓" if overall >= 7 else "△" if overall >= 5 else "✗"
    print(
        f"  ↳ Score: {overall}/10 {status}  "
        f"(acc={scores.get('accuracy')}, "
        f"comp={scores.get('completeness')}, "
        f"rel={scores.get('relevance')})  "
        f"[judge {judge_time}s]"
    )

    return {
        "id": cid,
        "category": case.get("category", ""),
        "question": question,
        "expected_answer": expected,
        "actual_answer": actual_answer,
        "scores": scores,
        "query_time_s": query_time,
        "judge_time_s": judge_time,
    }


# ── Main ──────────────────────────────────────────────────────────────────

async def main(
    ids: list[int] | None = None,
    category: str | None = None,
    report_path: Path = DEFAULT_REPORT_PATH,
    concurrency: int = 3,
):
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_cases = data["test_cases"]

    if ids:
        cases = [c for c in all_cases if c["id"] in ids]
    elif category:
        cases = [c for c in all_cases if c.get("category") == category]
    else:
        cases = all_cases

    if not cases:
        print("No test cases matched the filter.")
        sys.exit(1)

    total = len(cases)
    print(f"═══ FF Master RAG Evaluation ═══")
    print(f"Test cases: {total}")
    print(f"Assistant:  {OPENAI_ASSISTANT_ID}")
    print(f"Judge:      {JUDGE_MODEL}")
    print(f"Concurrency: {concurrency}")
    print(f"Report:     {report_path}")

    semaphore = asyncio.Semaphore(concurrency)
    results: list[dict] = []

    async def bounded(case: dict, idx: int) -> dict:
        async with semaphore:
            return await run_single(case, idx, total)

    tasks = [bounded(c, i + 1) for i, c in enumerate(cases)]
    results = await asyncio.gather(*tasks)

    # ── Summary ───────────────────────────────────────────────────────
    scores_overall = [r["scores"].get("overall", 0) for r in results]
    scores_acc = [r["scores"].get("accuracy", 0) for r in results]
    scores_comp = [r["scores"].get("completeness", 0) for r in results]
    scores_rel = [r["scores"].get("relevance", 0) for r in results]
    total_query_time = sum(r["query_time_s"] for r in results)

    avg = lambda xs: round(sum(xs) / len(xs), 2) if xs else 0
    pass_count = sum(1 for s in scores_overall if s >= 7)
    fail_count = sum(1 for s in scores_overall if s < 5)

    summary = {
        "total_cases": total,
        "pass_count_gte7": pass_count,
        "warning_count_5to7": total - pass_count - fail_count,
        "fail_count_lt5": fail_count,
        "pass_rate": f"{round(pass_count / total * 100, 1)}%",
        "avg_overall": avg(scores_overall),
        "avg_accuracy": avg(scores_acc),
        "avg_completeness": avg(scores_comp),
        "avg_relevance": avg(scores_rel),
        "total_query_time_s": round(total_query_time, 1),
    }

    # Category breakdown
    categories: dict[str, list[float]] = {}
    for r in results:
        cat = r.get("category", "other")
        categories.setdefault(cat, []).append(r["scores"].get("overall", 0))
    category_summary = {
        cat: {"count": len(scores), "avg_overall": avg(scores)}
        for cat, scores in sorted(categories.items())
    }

    report = {
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "assistant_id": OPENAI_ASSISTANT_ID,
            "judge_model": JUDGE_MODEL,
        },
        "summary": summary,
        "category_breakdown": category_summary,
        "results": sorted(results, key=lambda r: r["id"]),
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n{'═' * 50}")
    print(f"  总计: {total} 用例")
    print(f"  通过 (≥7): {pass_count}  ({summary['pass_rate']})")
    print(f"  警告 (5-7): {summary['warning_count_5to7']}")
    print(f"  失败 (<5):  {fail_count}")
    print(f"  平均综合分: {summary['avg_overall']}/10")
    print(f"  平均准确性: {summary['avg_accuracy']}/10")
    print(f"  平均完整性: {summary['avg_completeness']}/10")
    print(f"  平均相关性: {summary['avg_relevance']}/10")
    print(f"  RAG 总耗时: {summary['total_query_time_s']}s")
    print(f"{'═' * 50}")
    print(f"\n分类明细:")
    for cat, info in category_summary.items():
        print(f"  {cat:20s}  {info['count']} cases  avg={info['avg_overall']}/10")
    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FF Master RAG Evaluation")
    parser.add_argument("--ids", type=int, nargs="+", help="Run specific test case IDs")
    parser.add_argument("--category", type=str, help="Run cases in a specific category")
    parser.add_argument(
        "--report", type=str, default=str(DEFAULT_REPORT_PATH),
        help="Output report path",
    )
    parser.add_argument(
        "--concurrency", type=int, default=3,
        help="Max concurrent RAG queries (default: 3)",
    )
    args = parser.parse_args()

    asyncio.run(
        main(
            ids=args.ids,
            category=args.category,
            report_path=Path(args.report),
            concurrency=args.concurrency,
        )
    )
