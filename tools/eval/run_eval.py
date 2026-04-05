"""
FF Robot RAG Evaluation Script (V3)

Uses the production Plan → Loop (domain agents) → Output pipeline by default:
  1. Plan Agent — routing, domain flags (product / price / news), query expansion
  2. Loop — Product / Price / News retrieval agents (non-streamed)
  3. Output Agent — streamed final answer

Pass --no-triage to fall back to a simple single-agent mode (legacy).

Evaluation phases:
  Phase 1 — Query the RAG system once per test case.
  Phase 2 — Score each answer with one or more Judge models (quality + claim recall).

Scoring dimensions (4 core + claim recall):
  Correctness, Faithfulness, Relevance, Citation, Claim Recall

Usage:
    cd tools/eval
    python run_eval.py                                        # all cases (with triage)
    python run_eval.py --no-triage                            # legacy single-agent mode
    python run_eval.py --ids 1 2 3                            # specific cases
    python run_eval.py --category safety                      # by category
    python run_eval.py --question-type user_rewrite           # by question type
    python run_eval.py --judge-models gpt-4o gpt-4.1 o1      # multi-judge
    python run_eval.py --repeat 3                             # consistency test
    python run_eval.py --min-pass-rate 80                     # CI gate

Environment variables (via .env or shell):
    OPENAI_API_KEY                      — Required. OpenAI API key.
    OPENAI_VECTOR_STORE_ROBOT_ALL_ID    — All-products vector store (used as fallback).
    OPENAI_VECTOR_STORE_ID              — Legacy single-store ID (used by --no-triage).
    OPENAI_VECTOR_STORE_MASTER_ULTRA_ID — Per-product store (optional, falls back to ALL).
    OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID
    OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID
    OPENAI_VECTOR_STORE_AEGIS_EDU_ID
    LLM_MODEL                           — Model for Support Agent (default: gpt-4o).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parent.parent
_RAG_ROOT = REPO_ROOT / "apps" / "rag-api"
if str(_RAG_ROOT) not in sys.path:
    sys.path.insert(0, str(_RAG_ROOT))

_env_local = EVAL_DIR / ".env"
_env_root = REPO_ROOT / ".env"
_env_rag_api = _RAG_ROOT / ".env"
if _env_local.exists():
    load_dotenv(_env_local)
elif _env_root.exists():
    load_dotenv(_env_root)
elif _env_rag_api.exists():
    load_dotenv(_env_rag_api)
else:
    load_dotenv()

from agents import Agent, FileSearchTool, ModelSettings, Runner
from openai import AsyncOpenAI
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_VECTOR_STORE_ID: str = os.getenv("OPENAI_VECTOR_STORE_ID", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")

# ── Per-product vector store IDs (fallback to OPENAI_VECTOR_STORE_ID) ────

OPENAI_VECTOR_STORE_MASTER_ULTRA_ID: str = os.getenv("OPENAI_VECTOR_STORE_MASTER_ULTRA_ID", "")
OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID: str = os.getenv("OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID", "")
OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID: str = os.getenv("OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID", "")
OPENAI_VECTOR_STORE_AEGIS_EDU_ID: str = os.getenv("OPENAI_VECTOR_STORE_AEGIS_EDU_ID", "")
OPENAI_VECTOR_STORE_ROBOT_ALL_ID: str = os.getenv("OPENAI_VECTOR_STORE_ROBOT_ALL_ID", "")

_FALLBACK_VECTOR_STORE_ID = OPENAI_VECTOR_STORE_ROBOT_ALL_ID or OPENAI_VECTOR_STORE_ID

# ── Production instructions path ─────────────────────────────────────────

_INSTRUCTIONS_DIR = _RAG_ROOT / "app" / "services" / "instructions"


def _load_instructions(name: str) -> str:
    return (_INSTRUCTIONS_DIR / f"{name}.md").read_text(encoding="utf-8")


from app.services.recommendation_engine import RecommendationEngine
from app.services.chatkit_handler import (
    TriageOutput,
    _build_loop_domain_agent,
    _build_output_agent,
    _plan_loop_passes,
)

# ── Plan Agent (mirrors production chatkit_handler.py schema) ────────────

_TRIAGE_MODEL_SETTINGS = ModelSettings(store=False)

_reco_engine = RecommendationEngine()
_TRIAGE_INSTRUCTIONS = (
    _load_instructions("triage")
    .replace("{{recommendation_rules}}", _reco_engine.build_triage_rules_prompt())
    .replace("{{purchase_intent_rules}}", _reco_engine.build_purchase_intent_prompt())
)

triage_agent = Agent(
    name="FF Robot Plan",
    instructions=_TRIAGE_INSTRUCTIONS,
    model="gpt-4o",
    output_type=TriageOutput,
    model_settings=_TRIAGE_MODEL_SETTINGS,
)


# ── Legacy simple agent (used when --no-triage is set) ───────────────────

_DEFAULT_INSTRUCTIONS = """\
You are an expert assistant for FF humanoid robot user manuals.
Answer the user's question based ONLY on the documents retrieved via file_search.
If the documents do not contain relevant information, state that explicitly.

Rules:
1. Always use file_search to find relevant information before answering.
2. Be concise, professional, and structured (use lists/tables when appropriate).
3. If documents contain image references (e.g. ![alt](/images/...)), preserve them.
4. Do NOT fabricate information not found in the documents.
5. Do NOT manually add citation marks — the system handles citation display.\
"""

_instructions_file = os.getenv("INSTRUCTIONS_FILE", "")
if _instructions_file:
    _inst_path = Path(_instructions_file)
    if not _inst_path.is_absolute():
        _inst_path = EVAL_DIR / _inst_path
    AGENT_INSTRUCTIONS = _inst_path.read_text(encoding="utf-8")
else:
    AGENT_INSTRUCTIONS = _DEFAULT_INSTRUCTIONS

TEST_CASES_PATH = EVAL_DIR / "test_cases.json"
DEFAULT_REPORT_DIR = EVAL_DIR / "reports"
DEFAULT_ANSWERS_DIR = EVAL_DIR / "answers"
HISTORY_PATH = EVAL_DIR / "history.json"

DEFAULT_JUDGE_MODEL = "gpt-4o"
MAX_RETRIES = 3
RETRY_DELAY_S = 5

oai = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ── Score keys & empty template ──────────────────────────────────────────

SCORE_KEYS = ["correctness", "faithfulness", "relevance", "citation", "overall"]

EMPTY_SCORES: dict = {k: 0 for k in SCORE_KEYS}

# ── Judge prompt (with calibration anchors + error taxonomy) ─────────────

JUDGE_SYSTEM_PROMPT = """\
You are an expert evaluator for a RAG (Retrieval-Augmented Generation) system \
that answers questions about the FF Master humanoid robot user manual.

You will receive:
- **Question**: the user's question
- **Expected Answer**: the ground-truth reference answer
- **Actual Answer**: the RAG system's response

Score the Actual Answer on four dimensions (each 0-10):

### 1. Correctness (0-10)
Are the facts, numbers, procedures, and conclusions correct?
- 10: Every fact matches the expected answer exactly.
- 7: Core facts correct; minor omissions or imprecise wording.
- 5: Some facts correct, some wrong or missing key details.
- 3: Major factual errors (wrong numbers, wrong procedures).
- 0: Entirely wrong or contradicts the expected answer.
NOTE: Do NOT deduct here for missing information — that is measured by Claim Recall separately. \
Only deduct for *incorrect* information.

### 2. Faithfulness (0-10)
Is the answer grounded in evidence from the user manual, rather than fabricated?
- 10: Every statement can be traced to the manual; nothing invented.
- 7: Mostly grounded; minor extrapolations that are reasonable.
- 5: Mix of grounded and unverifiable statements.
- 3: Significant fabrication — plausible-sounding but unsupported claims.
- 0: Entirely fabricated / hallucinated.
For questions about topics NOT in the manual, the system should explicitly state \
"the manual does not cover this" rather than guessing. If it does so, give 10. \
If it guesses or fabricates, give 0-3.

### 3. Relevance (0-10)
Is the answer focused on the question and free of off-topic content?
- 10: Directly and concisely answers the question.
- 7: Answers the question but includes some unnecessary information.
- 5: Partially relevant; significant off-topic content.
- 3: Mostly off-topic.
- 0: Completely irrelevant.

### 4. Citation (0-10)
Does the answer reference source documents correctly?
- 10: Correct citations present (e.g. 【...†source】 pointing to right files).
- 7: Citations present but some point to wrong sections.
- 5: No explicit citations, but answer is correct.
- 3: No citations and answer quality is poor.
- 0: Wrong citations that mislead the reader.

### Error Taxonomy
Also identify which error types apply. Choose ALL that apply from this list \
(empty list if no errors):
- retrieval_miss: The answer lacks key information that should have been retrieved.
- wrong_number: A specific number/value is incorrect.
- wrong_unit: The unit of measurement is wrong.
- wrong_procedure: Steps or procedures are incorrect or in wrong order.
- unsupported_claim: Contains claims not backed by the manual.
- partial_answer: Answer is correct but significantly incomplete.
- over_refusal: Refused to answer when the information IS in the manual.
- under_refusal: Guessed/fabricated when the topic is NOT in the manual.
- citation_wrong: Citations point to incorrect documents.
- citation_missing: Should have citations but doesn't.
- irrelevant_content: Contains significant off-topic information.

Respond with ONLY valid JSON (no markdown fences):
{
  "correctness": <0-10>,
  "faithfulness": <0-10>,
  "relevance": <0-10>,
  "citation": <0-10>,
  "overall": <float>,
  "error_tags": ["tag1", "tag2"],
  "comment": "<brief explanation in Chinese, 1-3 sentences>"
}

The "overall" score is a weighted average: \
correctness×0.35 + faithfulness×0.30 + relevance×0.20 + citation×0.15, \
rounded to 1 decimal.\
"""

# ── Claim Recall prompt (RAGAS-style claim decomposition) ────────────────

CLAIM_RECALL_PROMPT = """\
You are an expert evaluator measuring Claim Recall for a RAG system.

You will receive:
- **Expected Answer**: the ground-truth reference answer
- **Actual Answer**: the RAG system's response

Your task:
1. Break the Expected Answer into individual **claims** (atomic factual statements).
   Each claim should be a single, verifiable piece of information.
2. For each claim, determine if the Actual Answer **supports** it (verdict = 1) or
   **does not support / contradicts** it (verdict = 0).
   A claim is "supported" if the Actual Answer contains equivalent information,
   even if worded differently.

Respond with ONLY valid JSON (no markdown fences):
{
  "claims": [
    {"claim": "<claim text>", "verdict": 0 or 1},
    ...
  ],
  "recall": <float 0.0-1.0>
}

Be strict: if the Actual Answer gives a WRONG value for a claim (e.g. wrong number, \
wrong procedure), that claim's verdict must be 0.\
"""


# ── Query the RAG agent (Agents SDK + FileSearchTool, with retry) ─────────

USE_TRIAGE: bool = True


def _extract_answer_with_citations(result) -> str:
    """Extract the text answer and append file citations from raw_responses."""
    text = result.final_output
    if not isinstance(text, str):
        text = str(text)
    text = text.strip()

    cited_files: list[str] = []
    for resp in result.raw_responses:
        for item in getattr(resp, "output", []):
            for content_part in getattr(item, "content", []):
                for ann in getattr(content_part, "annotations", []):
                    fname = getattr(ann, "filename", None)
                    if fname and fname not in cited_files:
                        cited_files.append(fname)

    if cited_files:
        refs = " ".join(f"【{f}】" for f in cited_files)
        text = f"{text}\n\nSources: {refs}"

    return text


async def ask_agent(question: str, retries: int = MAX_RETRIES) -> str:
    if USE_TRIAGE:
        return await _ask_with_triage(question, retries)
    return await _ask_simple(question, retries)


async def _ask_with_triage(question: str, retries: int) -> str:
    """Production-equivalent flow: Plan → Loop (domain agents) → Output."""
    for attempt in range(1, retries + 1):
        try:
            triage_result = await Runner.run(triage_agent, input=question)
            triage_output: TriageOutput = triage_result.final_output
            print(
                f"  ◆ Plan → type={triage_output.query_type}, "
                f"product_types={triage_output.product_types}, "
                f"lang={triage_output.input_lang}, "
                f"domains product={triage_output.needs_product} "
                f"price={triage_output.needs_price} news={triage_output.needs_news}, "
                f"query={triage_output.query_text[:80]}…"
            )

            loop_passes = _plan_loop_passes(triage_output)
            conversation = [{"role": "user", "content": triage_output.query_text}]
            retrieval_results: list[tuple[str, str]] = []

            for pass_info in loop_passes:
                domain_agent = _build_loop_domain_agent(triage_output, pass_info)
                pass_result = await Runner.run(domain_agent, input=conversation)
                pass_text = pass_result.final_output
                if not isinstance(pass_text, str):
                    pass_text = str(pass_text)
                retrieval_results.append((pass_info.focus_label, pass_text))

            output_agent = _build_output_agent(
                triage_output.input_lang,
                triage_output.query_text,
                retrieval_results,
            )
            result = await Runner.run(output_agent, input=conversation)
            return _extract_answer_with_citations(result)
        except Exception as e:
            if attempt < retries:
                print(f"  ⚠ Attempt {attempt} failed: {e}. Retrying in {RETRY_DELAY_S}s...")
                await asyncio.sleep(RETRY_DELAY_S)
            else:
                print(f"  ✗ All {retries} attempts failed: {e}")
                return f"[ERROR] {e}"
    return "[ERROR] Unexpected retry exhaustion"


async def _ask_simple(question: str, retries: int) -> str:
    """Legacy single-agent flow (no triage). Used with --no-triage."""
    instructions = AGENT_INSTRUCTIONS
    if "{{query_text}}" in instructions:
        instructions = instructions.replace("{{query_text}}", question)
    if "{{input_lang}}" in instructions:
        instructions = instructions.replace("{{input_lang}}", "en")

    agent = Agent(
        name="Eval RAG Agent",
        instructions=instructions,
        model=LLM_MODEL,
        tools=[FileSearchTool(vector_store_ids=[OPENAI_VECTOR_STORE_ID])],
        model_settings=ModelSettings(tool_choice="required"),
    )

    for attempt in range(1, retries + 1):
        try:
            result = await Runner.run(agent, input=question)
            return _extract_answer_with_citations(result)
        except Exception as e:
            if attempt < retries:
                print(f"  ⚠ Attempt {attempt} failed: {e}. Retrying in {RETRY_DELAY_S}s...")
                await asyncio.sleep(RETRY_DELAY_S)
            else:
                print(f"  ✗ All {retries} attempts failed: {e}")
                return f"[ERROR] {e}"
    return "[ERROR] Unexpected retry exhaustion"


# ── Judge: quality scoring ───────────────────────────────────────────────

async def judge_answer(
    question: str, expected: str, actual: str,
    model: str = DEFAULT_JUDGE_MODEL, retries: int = MAX_RETRIES,
) -> dict:
    user_content = (
        f"**Question**: {question}\n\n"
        f"**Expected Answer**: {expected}\n\n"
        f"**Actual Answer**: {actual}"
    )
    is_o_series = model.startswith("o")
    for attempt in range(1, retries + 1):
        try:
            kw: dict = {
                "model": model,
                "messages": [
                    {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                "response_format": {"type": "json_object"},
            }
            if not is_o_series:
                kw["temperature"] = 0.1
            resp = await oai.chat.completions.create(**kw)
            raw = resp.choices[0].message.content or "{}"
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {**EMPTY_SCORES, "error_tags": [], "comment": f"Parse error: {raw[:200]}"}
        except Exception as e:
            if attempt < retries:
                print(f"  ⚠ Judge ({model}) attempt {attempt} failed: {e}. Retrying...")
                await asyncio.sleep(RETRY_DELAY_S)
            else:
                return {**EMPTY_SCORES, "error_tags": [], "comment": f"Judge failed: {e}"}
    return {**EMPTY_SCORES, "error_tags": [], "comment": "Retry exhaustion"}


# ── Judge: claim recall ──────────────────────────────────────────────────

async def judge_claim_recall(
    expected: str, actual: str,
    model: str = DEFAULT_JUDGE_MODEL, retries: int = MAX_RETRIES,
) -> dict:
    user_content = (
        f"**Expected Answer**: {expected}\n\n"
        f"**Actual Answer**: {actual}"
    )
    is_o_series = model.startswith("o")
    for attempt in range(1, retries + 1):
        try:
            kw: dict = {
                "model": model,
                "messages": [
                    {"role": "system", "content": CLAIM_RECALL_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                "response_format": {"type": "json_object"},
            }
            if not is_o_series:
                kw["temperature"] = 0.1
            resp = await oai.chat.completions.create(**kw)
            raw = resp.choices[0].message.content or "{}"
            try:
                parsed = json.loads(raw)
                claims = parsed.get("claims", [])
                supported = sum(1 for c in claims if c.get("verdict") == 1)
                recall = round(supported / len(claims), 4) if claims else 0.0
                return {
                    "claims": claims,
                    "total_claims": len(claims),
                    "supported_claims": supported,
                    "recall": recall,
                }
            except json.JSONDecodeError:
                pass
        except Exception as e:
            if attempt < retries:
                await asyncio.sleep(RETRY_DELAY_S)
    return {"claims": [], "total_claims": 0, "supported_claims": 0, "recall": 0.0}


# ── Phase 1: Query RAG ───────────────────────────────────────────────────

async def query_rag(case: dict, index: int, total: int, max_query_time: float) -> dict:
    cid = case["id"]
    question = case["question"]
    print(f"\n[{index}/{total}] Case #{cid}: {question[:60]}...")
    t0 = time.time()
    actual_answer = await ask_agent(question)
    query_time = round(time.time() - t0, 2)
    time_warning = f" ⚠ SLOW (>{max_query_time}s)" if query_time > max_query_time else ""
    print(f"  ↳ RAG responded in {query_time}s ({len(actual_answer)} chars){time_warning}")
    return {
        "id": cid,
        "category": case.get("category", ""),
        "question_type": case.get("question_type", "doc_extraction"),
        "question": question,
        "expected_answer": case["expected_answer"],
        "actual_answer": actual_answer,
        "query_time_s": query_time,
        "slow": query_time > max_query_time,
    }


# ── Phase 2: Judge all results with one model ────────────────────────────

async def judge_all(rag_results: list[dict], model: str, concurrency: int) -> list[dict]:
    total = len(rag_results)
    print(f"\n{'─' * 55}")
    print(f"  Judging with: {model}  ({total} cases)")
    print(f"{'─' * 55}")
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded(r: dict, idx: int) -> dict:
        async with semaphore:
            t0 = time.time()
            scores_task = judge_answer(
                r["question"], r["expected_answer"], r["actual_answer"], model=model,
            )
            recall_task = judge_claim_recall(
                r["expected_answer"], r["actual_answer"], model=model,
            )
            scores, recall_result = await asyncio.gather(scores_task, recall_task)
            judge_time = round(time.time() - t0, 2)

            overall = scores.get("overall", 0)
            recall_val = recall_result.get("recall", 0)
            tags = scores.get("error_tags", [])
            status = "✓" if overall >= 7 else "△" if overall >= 5 else "✗"
            tag_str = f"  tags={','.join(tags)}" if tags else ""
            print(
                f"  [{idx}/{total}] #{r['id']} {status} {overall}/10  "
                f"recall={recall_val:.0%}  "
                f"(cor={scores.get('correctness')}, "
                f"fai={scores.get('faithfulness')}, "
                f"rel={scores.get('relevance')}, "
                f"cit={scores.get('citation')})"
                f"{tag_str}  [{judge_time}s]"
            )
            return {**r, "scores": scores, "claim_recall": recall_result, "judge_time_s": judge_time}

    tasks = [bounded(r, i + 1) for i, r in enumerate(rag_results)]
    return list(await asyncio.gather(*tasks))


# ── Helpers ──────────────────────────────────────────────────────────────

def safe_avg(xs: list[float]) -> float:
    return round(sum(xs) / len(xs), 2) if xs else 0


def build_summary(results: list[dict], max_query_time: float) -> dict:
    total = len(results)
    scores_by_key = {k: [r["scores"].get(k, 0) for r in results] for k in SCORE_KEYS}

    # Claim recall
    recall_scores = [r.get("claim_recall", {}).get("recall", 0) for r in results]
    total_claims = sum(r.get("claim_recall", {}).get("total_claims", 0) for r in results)
    supported_claims = sum(r.get("claim_recall", {}).get("supported_claims", 0) for r in results)
    avg_claim_recall = round(sum(recall_scores) / len(recall_scores), 4) if recall_scores else 0
    global_claim_recall = round(supported_claims / total_claims, 4) if total_claims else 0

    # Pass / fail
    total_query_time = sum(r["query_time_s"] for r in results)
    slow_count = sum(1 for r in results if r.get("slow"))
    pass_count = sum(1 for s in scores_by_key["overall"] if s >= 7)
    fail_count = sum(1 for s in scores_by_key["overall"] if s < 5)
    pass_rate_pct = round(pass_count / total * 100, 1) if total else 0

    # ── Red-line metrics ─────────────────────────────────────────────
    safety_results = [r for r in results if r.get("category") == "safety"]
    safety_catastrophic = sum(
        1 for r in safety_results if r["scores"].get("correctness", 0) < 3
    )

    negative_results = [r for r in results if r.get("category") == "negative"]
    negative_unsafe = sum(
        1 for r in negative_results if "under_refusal" in r["scores"].get("error_tags", [])
    )
    negative_unsafe_rate = round(
        negative_unsafe / len(negative_results) * 100, 1
    ) if negative_results else 0

    spec_results = [r for r in results if r.get("category") == "specifications"]
    spec_correct = sum(
        1 for r in spec_results if r["scores"].get("correctness", 0) >= 7
    )
    spec_exactness_pct = round(
        spec_correct / len(spec_results) * 100, 1
    ) if spec_results else 0

    # ── Error tag aggregation ────────────────────────────────────────
    all_tags: dict[str, int] = {}
    for r in results:
        for tag in r["scores"].get("error_tags", []):
            all_tags[tag] = all_tags.get(tag, 0) + 1

    # ── Question type breakdown ─────────────────────────────────────
    qt_overall: dict[str, list[float]] = {}
    qt_recall: dict[str, list[float]] = {}
    qt_pass: dict[str, int] = {}
    qt_count: dict[str, int] = {}
    for r in results:
        qt = r.get("question_type", "doc_extraction")
        qt_overall.setdefault(qt, []).append(r["scores"].get("overall", 0))
        qt_recall.setdefault(qt, []).append(r.get("claim_recall", {}).get("recall", 0))
        qt_count[qt] = qt_count.get(qt, 0) + 1
        if r["scores"].get("overall", 0) >= 7:
            qt_pass[qt] = qt_pass.get(qt, 0) + 1

    question_type_breakdown = {
        qt: {
            "count": qt_count.get(qt, 0),
            "avg_overall": safe_avg(qt_overall.get(qt, [])),
            "avg_claim_recall": round(safe_avg(qt_recall.get(qt, [])), 4),
            "pass_count": qt_pass.get(qt, 0),
            "pass_rate": f"{round(qt_pass.get(qt, 0) / qt_count[qt] * 100, 1)}%"
            if qt_count.get(qt) else "0%",
        }
        for qt in sorted(qt_overall.keys())
    }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_cases": total,
        "pass_count_gte7": pass_count,
        "warning_count_5to7": total - pass_count - fail_count,
        "fail_count_lt5": fail_count,
        "pass_rate": f"{pass_rate_pct}%",
        "pass_rate_pct": pass_rate_pct,
        **{f"avg_{k}": safe_avg(scores_by_key[k]) for k in SCORE_KEYS},
        "avg_claim_recall": avg_claim_recall,
        "global_claim_recall": global_claim_recall,
        "total_claims": total_claims,
        "supported_claims": supported_claims,
        "total_query_time_s": round(total_query_time, 1),
        "slow_count": slow_count,
        "max_query_time_threshold_s": max_query_time,
        "redline": {
            "safety_catastrophic_fails": safety_catastrophic,
            "safety_total": len(safety_results),
            "negative_unsafe_rate": f"{negative_unsafe_rate}%",
            "negative_unsafe_count": negative_unsafe,
            "negative_total": len(negative_results),
            "spec_exactness": f"{spec_exactness_pct}%",
            "spec_correct_count": spec_correct,
            "spec_total": len(spec_results),
        },
        "error_tag_distribution": dict(sorted(all_tags.items(), key=lambda x: -x[1])),
        "question_type_breakdown": question_type_breakdown,
    }


def build_category_breakdown(results: list[dict]) -> dict:
    cat_overall: dict[str, list[float]] = {}
    cat_recall: dict[str, list[float]] = {}
    for r in results:
        cat = r.get("category", "other")
        cat_overall.setdefault(cat, []).append(r["scores"].get("overall", 0))
        cat_recall.setdefault(cat, []).append(r.get("claim_recall", {}).get("recall", 0))
    return {
        cat: {
            "count": len(scores),
            "avg_overall": safe_avg(scores),
            "avg_claim_recall": round(safe_avg(cat_recall.get(cat, [])), 4),
        }
        for cat, scores in sorted(cat_overall.items())
    }


def print_summary(summary: dict, model: str, max_query_time: float) -> None:
    rl = summary.get("redline", {})
    print(f"\n{'═' * 60}")
    print(f"  Judge Model:      {model}")
    print(f"  总计: {summary['total_cases']} 用例")
    print(f"  通过 (≥7):        {summary['pass_count_gte7']}  ({summary['pass_rate']})")
    print(f"  警告 (5-7):       {summary['warning_count_5to7']}")
    print(f"  失败 (<5):        {summary['fail_count_lt5']}")
    print(f"  ──────────────────────────────────────")
    print(f"  平均综合分:       {summary['avg_overall']}/10")
    print(f"  平均正确性:       {summary['avg_correctness']}/10")
    print(f"  平均忠实度:       {summary['avg_faithfulness']}/10")
    print(f"  平均相关性:       {summary['avg_relevance']}/10")
    print(f"  平均引用质量:     {summary['avg_citation']}/10")
    print(f"  Claim Recall:     {summary.get('avg_claim_recall', 0):.1%} (avg)")
    print(f"  Global Recall:    {summary.get('global_claim_recall', 0):.1%} "
          f"({summary.get('supported_claims', 0)}/{summary.get('total_claims', 0)})")
    print(f"  ──────────────────────────────────────")
    print(f"  🚨 安全红线:      {rl.get('safety_catastrophic_fails', 0)} 严重错误 / {rl.get('safety_total', 0)} 安全用例")
    print(f"  🚨 拒答失败率:    {rl.get('negative_unsafe_rate', '0%')} ({rl.get('negative_unsafe_count', 0)}/{rl.get('negative_total', 0)})")
    print(f"  🚨 规格精确率:    {rl.get('spec_exactness', '0%')} ({rl.get('spec_correct_count', 0)}/{rl.get('spec_total', 0)})")
    print(f"  ──────────────────────────────────────")
    print(f"  RAG 总耗时:       {summary['total_query_time_s']}s")
    if summary["slow_count"]:
        print(f"  ⚠ 慢响应 (>{max_query_time}s): {summary['slow_count']} 个")

    qt_breakdown = summary.get("question_type_breakdown", {})
    if qt_breakdown:
        print(f"  ──────────────────────────────────────")
        print(f"  按问题类型:")
        for qt, info in qt_breakdown.items():
            print(f"    {qt:20s}  {info['count']} cases  avg={info['avg_overall']}/10  "
                  f"pass={info['pass_rate']}  recall={info.get('avg_claim_recall', 0):.0%}")

    tags = summary.get("error_tag_distribution", {})
    if tags:
        print(f"  ──────────────────────────────────────")
        print(f"  错误分布 (top):")
        for tag, cnt in list(tags.items())[:8]:
            print(f"    {tag:25s}  {cnt} 次")
    print(f"{'═' * 60}")


# ── History tracking ─────────────────────────────────────────────────────

def append_history(summary: dict, report_path: str, model: str) -> None:
    history: list[dict] = []
    if HISTORY_PATH.exists():
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, ValueError):
            history = []
    history.append({
        "timestamp": summary["timestamp"],
        "judge_model": model,
        "report_file": str(report_path),
        "total_cases": summary["total_cases"],
        "pass_rate": summary["pass_rate"],
        "avg_overall": summary["avg_overall"],
        "avg_correctness": summary["avg_correctness"],
        "avg_faithfulness": summary["avg_faithfulness"],
        "avg_relevance": summary["avg_relevance"],
        "avg_citation": summary["avg_citation"],
        "avg_claim_recall": summary.get("avg_claim_recall", 0),
        "global_claim_recall": summary.get("global_claim_recall", 0),
        "redline": summary.get("redline", {}),
        "total_query_time_s": summary["total_query_time_s"],
    })
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ── Main ──────────────────────────────────────────────────────────────────

async def main(
    ids: list[int] | None = None,
    category: str | None = None,
    question_type: str | None = None,
    report_path: Path | None = None,
    concurrency: int = 3,
    repeat: int = 1,
    min_pass_rate: float = 0.0,
    max_query_time: float = 30.0,
    judge_models: list[str] | None = None,
    safety_max_fails: int = 0,
    negative_max_unsafe_pct: float = 5.0,
    spec_min_exactness: float = 0.0,
):
    if judge_models is None:
        judge_models = [DEFAULT_JUDGE_MODEL]

    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    all_cases = data["test_cases"]

    if ids:
        cases = [c for c in all_cases if c["id"] in ids]
    elif category:
        cases = [c for c in all_cases if c.get("category") == category]
    elif question_type:
        cases = [c for c in all_cases if c.get("question_type") == question_type]
    else:
        cases = all_cases

    if not cases:
        print("No test cases matched the filter.")
        sys.exit(1)

    DEFAULT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if report_path is None:
        report_path = DEFAULT_REPORT_DIR / f"report_{ts}.json"

    total = len(cases)
    multi_judge = len(judge_models) > 1

    print(f"═══ FF Master RAG Evaluation V2 ═══")
    print(f"Test cases:     {total}")
    print(f"RAG model:      {LLM_MODEL}")
    print(f"Vector store:   {OPENAI_VECTOR_STORE_ID}")
    print(f"Judge models:   {', '.join(judge_models)}")
    print(f"Concurrency:    {concurrency}")
    print(f"Repeat:         {repeat}")
    print(f"Report:         {report_path}")

    # ── Phase 1: Query RAG ───────────────────────────────────────────
    all_run_rag_results: list[list[dict]] = []
    for run_idx in range(1, repeat + 1):
        label = f"RAG Query Run {run_idx}/{repeat}" if repeat > 1 else f"Phase 1: Querying RAG ({total} cases)"
        print(f"\n{'━' * 55}")
        print(f"  {label}")
        print(f"{'━' * 55}")
        sem = asyncio.Semaphore(concurrency)

        async def bq(case: dict, idx: int) -> dict:
            async with sem:
                return await query_rag(case, idx, total, max_query_time)

        tasks = [bq(c, i + 1) for i, c in enumerate(cases)]
        rag_results = list(await asyncio.gather(*tasks))
        all_run_rag_results.append(rag_results)

    rag_results = all_run_rag_results[-1]

    # ── Phase 2: Judge with each model ───────────────────────────────
    print(f"\n{'━' * 55}")
    print(f"  Phase 2: Judging ({len(judge_models)} model(s))")
    print(f"{'━' * 55}")

    model_scored: dict[str, list[dict]] = {}
    model_summaries: dict[str, dict] = {}
    model_categories: dict[str, dict] = {}

    for model in judge_models:
        scored = await judge_all(rag_results, model, concurrency)
        model_scored[model] = scored
        summary = build_summary(scored, max_query_time)
        model_summaries[model] = summary
        cat_breakdown = build_category_breakdown(scored)
        model_categories[model] = cat_breakdown
        print_summary(summary, model, max_query_time)
        print(f"\n  分类明细 ({model}):")
        for cat, info in cat_breakdown.items():
            print(f"    {cat:20s}  {info['count']} cases  avg={info['avg_overall']}/10  recall={info.get('avg_claim_recall', 0):.0%}")

    # ── Consistency analysis ─────────────────────────────────────────
    consistency: dict | None = None
    primary_model = judge_models[0]

    if repeat > 1:
        per_case_scores: dict[int, list[float]] = {}
        for run_rag in all_run_rag_results:
            scored_run = await judge_all(run_rag, primary_model, concurrency)
            for r in scored_run:
                per_case_scores.setdefault(r["id"], []).append(r["scores"].get("overall", 0))
        consistency_details = []
        for cid, scores_list in sorted(per_case_scores.items()):
            stdev = round(statistics.stdev(scores_list), 2) if len(scores_list) > 1 else 0
            consistency_details.append({
                "id": cid, "scores": scores_list,
                "mean": round(statistics.mean(scores_list), 2),
                "stdev": stdev, "stable": stdev <= 1.0,
            })
        unstable = [d for d in consistency_details if not d["stable"]]
        consistency = {
            "judge_model": primary_model, "repeat_count": repeat,
            "total_cases": len(consistency_details),
            "unstable_cases": len(unstable),
            "unstable_case_ids": [d["id"] for d in unstable],
            "details": consistency_details,
        }

    # ── Build JSON report ────────────────────────────────────────────
    primary_results = model_scored[primary_model]
    report: dict = {
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rag_model": LLM_MODEL,
            "vector_store_id": OPENAI_VECTOR_STORE_ID,
            "judge_models": judge_models,
            "primary_judge_model": primary_model,
            "repeat_count": repeat,
            "scoring_dimensions": ["correctness", "faithfulness", "relevance", "citation"],
            "weights": "correctness×0.35 + faithfulness×0.30 + relevance×0.20 + citation×0.15",
        },
        "summary": model_summaries[primary_model],
        "category_breakdown": model_categories[primary_model],
        "question_type_breakdown": model_summaries[primary_model].get("question_type_breakdown", {}),
        "results": sorted(primary_results, key=lambda r: r["id"]),
    }
    if multi_judge:
        report["multi_judge"] = {
            "per_model_summary": model_summaries,
            "per_model_category": model_categories,
        }
    if consistency:
        report["consistency"] = consistency

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ── Generate eval output folder ─────────────────────────────────
    run_dir = DEFAULT_ANSWERS_DIR / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    case_lookup = {c["id"]: c for c in all_cases}

    # 1) eval_result.json
    eval_result_path = run_dir / "eval_result.json"
    eval_result_data = []
    for r in sorted(primary_results, key=lambda x: x["id"]):
        original = case_lookup.get(r["id"], {})
        cr = r.get("claim_recall", {})
        entry: dict = {
            "id": r["id"],
            "category": r.get("category", ""),
            "question_type": r.get("question_type", "doc_extraction"),
            "question": r["question"],
            "source_file": original.get("source_file", ""),
            "LLM_answer": r["actual_answer"],
            "scores": {
                "correctness": r["scores"].get("correctness", 0),
                "faithfulness": r["scores"].get("faithfulness", 0),
                "relevance": r["scores"].get("relevance", 0),
                "citation": r["scores"].get("citation", 0),
                "overall": r["scores"].get("overall", 0),
                "comment": r["scores"].get("comment", ""),
            },
            "error_tags": r["scores"].get("error_tags", []),
            "claim_recall": {
                "score": cr.get("recall", 0),
                "supported_claims": cr.get("supported_claims", 0),
                "total_claims": cr.get("total_claims", 0),
                "claims": cr.get("claims", []),
            },
            "query_time_s": r["query_time_s"],
        }
        if multi_judge:
            entry["scores_by_model"] = {}
            for m in judge_models:
                m_map = {mr["id"]: mr for mr in model_scored[m]}
                mr = m_map.get(r["id"])
                if mr:
                    entry["scores_by_model"][m] = {
                        k: mr["scores"].get(k, 0) for k in [*SCORE_KEYS, "comment"]
                    }
        eval_result_data.append(entry)

    with open(eval_result_path, "w", encoding="utf-8") as f:
        json.dump(eval_result_data, f, ensure_ascii=False, indent=2)

    # 2) summary_report.md
    summary_report_path = run_dir / "summary_report.md"
    ps = model_summaries[primary_model]
    rl = ps.get("redline", {})
    avg_qt = round(ps["total_query_time_s"] / total, 2) if total else 0
    error_tags = ps.get("error_tag_distribution", {})

    md = [
        "# RAG 评测报告",
        "",
        f"- **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **RAG 模型**: `{LLM_MODEL}`",
        f"- **Vector Store**: `{OPENAI_VECTOR_STORE_ID}`",
        f"- **评分模型**: {', '.join(judge_models)}",
        f"- **测试用例数**: {total}",
        f"- **评分维度**: Correctness×0.35 + Faithfulness×0.30 + Relevance×0.20 + Citation×0.15",
        "",
        "---",
        "",
        "## 总体评分",
        "",
        "| 指标 | 得分 |",
        "| --- | --- |",
        f"| 通过率 (≥7分) | **{ps['pass_rate']}** ({ps['pass_count_gte7']}/{total}) |",
        f"| 平均综合分 | **{ps['avg_overall']}/10** |",
        f"| 平均正确性 (Correctness) | {ps['avg_correctness']}/10 |",
        f"| 平均忠实度 (Faithfulness) | {ps['avg_faithfulness']}/10 |",
        f"| 平均相关性 (Relevance) | {ps['avg_relevance']}/10 |",
        f"| 平均引用质量 (Citation) | {ps['avg_citation']}/10 |",
        "",
        "## Claim Recall（要点召回率）",
        "",
        "将期望答案拆解为独立 claims，逐条检查 RAG 回答是否覆盖。",
        "",
        "| 指标 | 值 |",
        "| --- | --- |",
        f"| 平均 Claim Recall | **{ps.get('avg_claim_recall', 0):.1%}** |",
        f"| 全局 Claim Recall | **{ps.get('global_claim_recall', 0):.1%}** ({ps.get('supported_claims', 0)}/{ps.get('total_claims', 0)} claims) |",
        "",
        "> 注：Claim Recall 衡量的是最终回答对期望要点的覆盖率，而非检索层的 Evidence Recall。",
        "> 区分：Claim Recall 高但 Faithfulness 低 → 可能是模型猜对而非检索到；",
        "> Claim Recall 低但 Faithfulness 高 → 可能是检索到了但生成时遗漏。",
        "",
        "---",
        "",
        "## 红线指标",
        "",
        "| 红线 | 状态 | 详情 |",
        "| --- | --- | --- |",
    ]

    safety_ok = rl.get("safety_catastrophic_fails", 0) == 0
    md.append(f"| 安全类严重错误 | {'✓ PASS' if safety_ok else '✗ FAIL'} | "
              f"{rl.get('safety_catastrophic_fails', 0)} 严重错误 / {rl.get('safety_total', 0)} 安全用例 |")

    neg_rate = float(rl.get("negative_unsafe_rate", "0%").rstrip("%"))
    neg_ok = neg_rate <= negative_max_unsafe_pct
    md.append(f"| 拒答失败率 (≤{negative_max_unsafe_pct}%) | {'✓ PASS' if neg_ok else '✗ FAIL'} | "
              f"{rl.get('negative_unsafe_rate', '0%')} ({rl.get('negative_unsafe_count', 0)}/{rl.get('negative_total', 0)}) |")

    spec_rate = float(rl.get("spec_exactness", "0%").rstrip("%"))
    spec_ok = spec_rate >= spec_min_exactness if spec_min_exactness > 0 else True
    spec_label = f"✓ PASS" if spec_ok else f"✗ FAIL"
    if spec_min_exactness > 0:
        md.append(f"| 规格精确率 (≥{spec_min_exactness}%) | {spec_label} | {rl.get('spec_exactness', '0%')} ({rl.get('spec_correct_count', 0)}/{rl.get('spec_total', 0)}) |")
    else:
        md.append(f"| 规格精确率 | {rl.get('spec_exactness', '0%')} | {rl.get('spec_correct_count', 0)}/{rl.get('spec_total', 0)} |")

    md += [
        "",
        "---",
        "",
        "## 错误分布",
        "",
        "| 错误类型 | 次数 | 说明 |",
        "| --- | --- | --- |",
    ]
    tag_desc = {
        "retrieval_miss": "关键信息未被检索到",
        "wrong_number": "数值/参数错误",
        "wrong_unit": "单位错误",
        "wrong_procedure": "步骤/流程错误",
        "unsupported_claim": "包含手册中不存在的声明",
        "partial_answer": "回答正确但严重不完整",
        "over_refusal": "手册有信息但拒绝回答",
        "under_refusal": "手册无信息但仍臆测回答",
        "citation_wrong": "引用指向错误文档",
        "citation_missing": "应有引用但缺失",
        "irrelevant_content": "包含大量无关内容",
    }
    for tag, cnt in error_tags.items():
        desc = tag_desc.get(tag, "")
        md.append(f"| {tag} | {cnt} | {desc} |")

    md += [
        "",
        "---",
        "",
        "## 分类明细",
        "",
        "| 分类 | 用例数 | 平均综合分 | Claim Recall |",
        "| --- | --- | --- | --- |",
    ]
    for cat, info in model_categories[primary_model].items():
        md.append(f"| {cat} | {info['count']} | {info['avg_overall']}/10 | {info.get('avg_claim_recall', 0):.0%} |")

    qt_breakdown = ps.get("question_type_breakdown", {})
    if qt_breakdown:
        qt_labels = {
            "doc_extraction": "A-文档抽取",
            "user_rewrite": "B-用户改写",
            "task_scenario": "C-任务场景",
            "boundary_risk": "D-不可答/风险",
        }
        md += [
            "",
            "---",
            "",
            "## 按问题类型分布",
            "",
            "| 问题类型 | 用例数 | 平均综合分 | 通过率 | Claim Recall |",
            "| --- | --- | --- | --- | --- |",
        ]
        for qt, info in qt_breakdown.items():
            label = qt_labels.get(qt, qt)
            md.append(
                f"| {label} | {info['count']} | {info['avg_overall']}/10 | "
                f"{info['pass_rate']} | {info.get('avg_claim_recall', 0):.0%} |"
            )

    md += [
        "",
        "---",
        "",
        "## 性能指标",
        "",
        "| 指标 | 值 |",
        "| --- | --- |",
        f"| RAG 总耗时 | {ps['total_query_time_s']}s |",
        f"| 平均响应时间 | {avg_qt}s |",
        f"| 慢响应数 (>{ps['max_query_time_threshold_s']}s) | {ps['slow_count']} |",
    ]

    if multi_judge:
        md += ["", "---", "", "## 多模型对比", ""]
        header = "| 指标 |"
        sep = "| --- |"
        for m in judge_models:
            header += f" {m} |"
            sep += " --- |"
        md += [header, sep]
        for key, label in [
            ("pass_rate", "通过率"), ("avg_overall", "平均综合分"),
            ("avg_correctness", "平均正确性"), ("avg_faithfulness", "平均忠实度"),
            ("avg_relevance", "平均相关性"), ("avg_citation", "平均引用质量"),
            ("avg_claim_recall", "Claim Recall"),
        ]:
            row = f"| {label} |"
            for m in judge_models:
                val = model_summaries[m].get(key, "N/A")
                if key == "avg_claim_recall" and isinstance(val, (int, float)):
                    row += f" {val:.1%} |"
                elif isinstance(val, float):
                    row += f" {val} |"
                else:
                    row += f" {val} |"
            md.append(row)

    # Failed cases
    failed = [r for r in sorted(primary_results, key=lambda x: x["scores"].get("overall", 0)) if r["scores"].get("overall", 0) < 5]
    if failed:
        md += ["", "---", "", "## 失败用例 (综合分 < 5)", "",
               "| ID | 分类 | 问题类型 | 综合分 | Recall | 错误标签 | 问题 |",
               "| --- | --- | --- | --- | --- | --- | --- |"]
        for r in failed:
            q = r["question"][:35].replace("|", "\\|")
            tags_str = ", ".join(r["scores"].get("error_tags", [])[:3])
            recall_str = f"{r.get('claim_recall', {}).get('recall', 0):.0%}"
            qt = r.get("question_type", "doc_extraction")
            md.append(f"| {r['id']} | {r.get('category', '')} | {qt} | {r['scores'].get('overall', 0)} | {recall_str} | {tags_str} | {q}... |")

    md.append("")
    with open(summary_report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    # ── Append to history ────────────────────────────────────────────
    for model in judge_models:
        append_history(model_summaries[model], report_path, model)

    # ── Print multi-model comparison (terminal) ──────────────────────
    if multi_judge:
        print(f"\n{'═' * 75}")
        print(f"  多模型对比")
        print(f"{'═' * 75}")
        header = f"  {'指标':<16s}"
        for m in judge_models:
            header += f"  {m:>12s}"
        print(header)
        print(f"  {'─' * (16 + 14 * len(judge_models))}")
        for key, label in [
            ("avg_overall", "平均综合分"), ("avg_correctness", "平均正确性"),
            ("avg_faithfulness", "平均忠实度"), ("avg_relevance", "平均相关性"),
            ("avg_citation", "平均引用质量"), ("avg_claim_recall", "Claim Recall"),
            ("pass_rate", "通过率"),
        ]:
            row = f"  {label:<16s}"
            for m in judge_models:
                val = model_summaries[m].get(key, "N/A")
                if key == "avg_claim_recall" and isinstance(val, (int, float)):
                    row += f"  {val:>11.1%}"
                elif isinstance(val, float):
                    row += f"  {val:>12.2f}"
                else:
                    row += f"  {str(val):>12s}"
            print(row)
        print(f"{'═' * 75}")

    if consistency:
        print(f"\n一致性分析 ({repeat} 次运行, judge={primary_model}):")
        if consistency["unstable_cases"] == 0:
            print(f"  ✓ 所有用例稳定 (标准差 ≤ 1.0)")
        else:
            print(f"  ⚠ {consistency['unstable_cases']} 个不稳定用例:")
            for d in consistency["details"]:
                if not d["stable"]:
                    print(f"    Case #{d['id']}: scores={d['scores']} stdev={d['stdev']}")

    print(f"\n详细报告:     {report_path}")
    print(f"评测结果:     {eval_result_path}")
    print(f"总体报告:     {summary_report_path}")
    print(f"历史记录:     {HISTORY_PATH}")

    # ── CI gate (pass rate + red lines) ──────────────────────────────
    ci_failed = False

    primary_pct = model_summaries[primary_model]["pass_rate_pct"]
    if min_pass_rate > 0 and primary_pct < min_pass_rate:
        print(f"\n✗ CI FAIL: pass rate {primary_pct}% < {min_pass_rate}%")
        ci_failed = True

    if safety_max_fails >= 0 and rl.get("safety_catastrophic_fails", 0) > safety_max_fails:
        print(f"\n✗ CI FAIL: safety catastrophic fails "
              f"{rl['safety_catastrophic_fails']} > {safety_max_fails}")
        ci_failed = True

    if negative_max_unsafe_pct < 100:
        actual_neg = float(rl.get("negative_unsafe_rate", "0%").rstrip("%"))
        if actual_neg > negative_max_unsafe_pct:
            print(f"\n✗ CI FAIL: negative unsafe rate {actual_neg}% > {negative_max_unsafe_pct}%")
            ci_failed = True

    if spec_min_exactness > 0:
        actual_spec = float(rl.get("spec_exactness", "0%").rstrip("%"))
        if actual_spec < spec_min_exactness:
            print(f"\n✗ CI FAIL: spec exactness {actual_spec}% < {spec_min_exactness}%")
            ci_failed = True

    if ci_failed:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FF Master RAG Evaluation V2")
    parser.add_argument("--ids", type=int, nargs="+", help="Run specific test case IDs")
    parser.add_argument("--category", type=str, help="Run cases in a specific category")
    parser.add_argument("--question-type", type=str, default=None,
                        choices=["doc_extraction", "user_rewrite", "task_scenario", "boundary_risk"],
                        help="Run cases of a specific question type")
    parser.add_argument("--report", type=str, default=None, help="Output report path")
    parser.add_argument("--concurrency", type=int, default=3, help="Max concurrent queries (default: 3)")
    parser.add_argument("--repeat", type=int, default=1, help="Repeat N times for consistency (default: 1)")
    parser.add_argument("--min-pass-rate", type=float, default=0, help="CI: min pass rate %% (default: 0)")
    parser.add_argument("--max-query-time", type=float, default=30, help="Slow query threshold in seconds (default: 30)")
    parser.add_argument("--judge-models", type=str, nargs="+", default=None,
                        help=f"Judge model(s) (default: {DEFAULT_JUDGE_MODEL})")
    parser.add_argument("--safety-max-fails", type=int, default=0,
                        help="CI: max allowed safety catastrophic fails (default: 0)")
    parser.add_argument("--negative-max-unsafe-pct", type=float, default=5.0,
                        help="CI: max allowed negative unsafe rate %% (default: 5)")
    parser.add_argument("--spec-min-exactness", type=float, default=0,
                        help="CI: min required spec exactness %% (default: 0 = disabled)")
    parser.add_argument("--no-triage", action="store_true",
                        help="Skip Triage Agent; use simple single-agent mode (legacy)")
    args = parser.parse_args()

    if args.no_triage:
        USE_TRIAGE = False  # noqa: F841 — read by ask_agent()
        print("⚠ Triage disabled — using legacy single-agent mode")
    else:
        print("◆ Using production Triage → Support Agent pipeline")

    asyncio.run(main(
        ids=args.ids,
        category=args.category,
        question_type=args.question_type,
        report_path=Path(args.report) if args.report else None,
        concurrency=args.concurrency,
        repeat=args.repeat,
        min_pass_rate=args.min_pass_rate,
        max_query_time=args.max_query_time,
        judge_models=args.judge_models,
        safety_max_fails=args.safety_max_fails,
        negative_max_unsafe_pct=args.negative_max_unsafe_pct,
        spec_min_exactness=args.spec_min_exactness,
    ))