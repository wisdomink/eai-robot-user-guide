#!/usr/bin/env python3
"""
FF Robot RAG 评测结果多角色分析工具

使用多 Agent 架构，从不同专家视角分析评测结果，生成综合分析报告。

专家角色：
  1. RAG 技术专家   — 检索质量、模型能力、架构优化
  2. 产品安全专家   — 操作安全、风险评估、合规审查
  3. 产品经理       — 用户体验、上线策略、业务影响
  4. QA 测试专家    — 测试覆盖度、失败模式、质量门禁
  5. 综合决策者     — 汇总各方意见，给出最终上线建议

用法：
    python analyze_eval.py                                    # 分析最新报告
    python analyze_eval.py --report reports/report_xxx.json   # 指定报告
    python analyze_eval.py --model gpt-4o                     # 指定分析模型
    python analyze_eval.py --compare reports/old.json         # 与旧版对比
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

EVAL_DIR = Path(__file__).resolve().parent

_env_local = EVAL_DIR / ".env"
_env_parent = EVAL_DIR.parent / ".env"
if _env_local.exists():
    load_dotenv(_env_local)
elif _env_parent.exists():
    load_dotenv(_env_parent)
else:
    load_dotenv()

from agents import Agent, ModelSettings, Runner
from openai import AsyncOpenAI
from openai.types.shared import Reasoning

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
DEFAULT_MODEL = "gpt-5.4"

oai = AsyncOpenAI(api_key=OPENAI_API_KEY)

REPORTS_DIR = EVAL_DIR / "reports"
ANSWERS_DIR = EVAL_DIR / "answers"

# ── 报告数据预处理 ────────────────────────────────────────────────────────


def load_report(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_latest_report() -> Path:
    reports = sorted(REPORTS_DIR.glob("report_*.json"))
    if not reports:
        print("❌ 没有找到评测报告。请先运行 run_eval.py")
        sys.exit(1)
    return reports[-1]


_INSTRUCTIONS_DIR = EVAL_DIR.parent / "app" / "services" / "instructions"


def _load_project_context() -> str:
    """Load key instruction files so the implementation advisor has real context."""
    sections = ["\n# 项目关键文件内容\n"]
    for name in ("triage", "general"):
        fpath = _INSTRUCTIONS_DIR / f"{name}.md"
        if fpath.exists():
            content = fpath.read_text(encoding="utf-8")
            sections.append(f"## {fpath.relative_to(EVAL_DIR.parent)} (当前内容)\n```\n{content}\n```\n")
    return "\n".join(sections)


def build_summary_context(report: dict, compare_report: dict | None = None) -> str:
    """Build a concise data context for the expert agents."""
    summary = report.get("summary", {})
    results = report.get("results", [])

    failed_cases = [r for r in results if r["scores"]["overall"] < 5]
    warning_cases = [r for r in results if 5 <= r["scores"]["overall"] < 7]

    lines = [
        "# 评测数据摘要",
        "",
        f"- 评测时间: {summary.get('timestamp', 'N/A')}",
        f"- 总用例数: {summary.get('total_cases', 0)}",
        f"- 通过率 (≥7): {summary.get('pass_rate', 'N/A')} ({summary.get('pass_count_gte7', 0)}/{summary.get('total_cases', 0)})",
        f"- 平均综合分: {summary.get('avg_overall', 0)}/10",
        f"- 平均正确性: {summary.get('avg_correctness', 0)}/10",
        f"- 平均忠实度: {summary.get('avg_faithfulness', 0)}/10",
        f"- 平均相关性: {summary.get('avg_relevance', 0)}/10",
        f"- 平均引用质量: {summary.get('avg_citation', 0)}/10",
        f"- Claim Recall: {summary.get('avg_claim_recall', 0):.1%}",
        "",
    ]

    # Redline
    redline = summary.get("redline", {})
    lines.extend([
        "## 安全红线",
        f"- 安全严重错误: {redline.get('safety_catastrophic_fails', 'N/A')} / {redline.get('safety_total', 'N/A')} 安全用例",
        f"- 拒答失败率: {redline.get('negative_unsafe_rate', 'N/A')} ({redline.get('negative_unsafe_count', 'N/A')}/{redline.get('negative_total', 'N/A')})",
        f"- 规格精确率: {redline.get('spec_exactness', 'N/A')}",
        "",
    ])

    # Question type breakdown
    qt_breakdown = summary.get("question_type_breakdown", {})
    lines.append("## 按问题类型")
    for qt, data in qt_breakdown.items():
        lines.append(
            f"- {qt}: {data['count']} 用例, 平均 {data['avg_overall']}/10, "
            f"通过率 {data['pass_rate']}, recall {data['avg_claim_recall']:.0%}"
        )
    lines.append("")

    # Error distribution
    error_dist = summary.get("error_tag_distribution", {})
    lines.append("## 错误类型分布")
    for tag, cnt in sorted(error_dist.items(), key=lambda x: -x[1]):
        lines.append(f"- {tag}: {cnt} 次")
    lines.append("")

    # Failed cases detail
    lines.append(f"## 失败用例详情 ({len(failed_cases)} 个, overall < 5)")
    for r in sorted(failed_cases, key=lambda x: x["scores"]["overall"]):
        s = r["scores"]
        cr = r.get("claim_recall", {})
        recall = cr.get("recall", 0) if isinstance(cr, dict) else 0
        lines.append(
            f"\n### 用例 #{r['id']} [{r['question_type']}] [{r['category']}] — {s['overall']}/10"
        )
        lines.append(f"**问题**: {r['question']}")
        lines.append(f"**期望答案**: {r['expected_answer'][:200]}…")
        lines.append(f"**实际答案**: {r['actual_answer'][:200]}…")
        lines.append(f"**错误标签**: {s.get('error_tags', [])}")
        lines.append(f"**评委评语**: {s.get('comment', '')}")
        lines.append(f"**Claim Recall**: {recall:.0%}")

    # Warning cases summary
    lines.append(f"\n## 警告用例概要 ({len(warning_cases)} 个, 5 ≤ overall < 7)")
    for r in sorted(warning_cases, key=lambda x: x["scores"]["overall"]):
        s = r["scores"]
        lines.append(
            f"- #{r['id']} [{r['question_type']}] [{r['category']}] "
            f"{s['overall']}/10 tags={s.get('error_tags', [])}"
        )

    # Category breakdown
    cat_breakdown = report.get("category_breakdown", {})
    lines.append("\n## 按分类明细")
    for cat, data in sorted(cat_breakdown.items()):
        lines.append(f"- {cat}: {data['count']} 用例, 平均 {data['avg_overall']}/10")

    # Comparison
    if compare_report:
        old_summary = compare_report.get("summary", {})
        lines.extend([
            "\n## 与上次评测对比",
            f"- 平均综合分: {old_summary.get('avg_overall', '?')} → {summary.get('avg_overall', '?')}",
            f"- 通过率: {old_summary.get('pass_rate', '?')} → {summary.get('pass_rate', '?')}",
            f"- 平均引用: {old_summary.get('avg_citation', '?')} → {summary.get('avg_citation', '?')}",
        ])
        old_errors = old_summary.get("error_tag_distribution", {})
        new_errors = summary.get("error_tag_distribution", {})
        all_tags = set(list(old_errors.keys()) + list(new_errors.keys()))
        lines.append("- 错误变化:")
        for tag in sorted(all_tags):
            old_cnt = old_errors.get(tag, 0)
            new_cnt = new_errors.get(tag, 0)
            if old_cnt != new_cnt:
                delta = new_cnt - old_cnt
                lines.append(f"  - {tag}: {old_cnt} → {new_cnt} ({'+' if delta > 0 else ''}{delta})")

    lines.append(_load_project_context())

    return "\n".join(lines)


# ── 专家 Agent 定义 ───────────────────────────────────────────────────────

EXPERT_CONFIGS = [
    {
        "name": "RAG 技术专家",
        "emoji": "🔧",
        "instructions": """\
你是一名 RAG（检索增强生成）系统技术专家。你的任务是从**技术架构**角度分析评测结果。

分析要求：
1. **检索质量评估**：分析 retrieval_miss 的根因，是 embedding 质量、chunk 策略还是 query 改写不足？
2. **生成质量评估**：unsupported_claim（幻觉）的严重程度和模式，是否集中在特定类型？
3. **引用机制评估**：citation_wrong 和 citation_missing 的根因
4. **多产品路由**：Triage Agent 的路由准确性，是否存在系统性偏差
5. **架构瓶颈**：当前 Triage → Support Agent 架构的局限性
6. **具体优化建议**：给出 3-5 条可落地的技术优化措施，按投入产出比排序

输出要求：
- 用中文回答
- 结构化输出（使用标题和列表）
- 每条结论都要引用具体的数据或用例编号
- 区分"快速修复"和"架构优化"两类建议
""",
    },
    {
        "name": "产品安全专家",
        "emoji": "⚠️",
        "instructions": """\
你是一名产品安全与合规专家，专注于机器人产品的安全风险评估。你的任务是从**安全和法律风险**角度分析评测结果。

分析要求：
1. **操作安全风险**：重点审查 wrong_procedure 用例，评估错误操作步骤可能造成的后果（设备损坏/人身伤害）
2. **信息可靠性风险**：分析 unsupported_claim 和 under_refusal 用例，评估虚假信息的法律风险
3. **安全指导缺失**：分析 over_refusal 用例，当系统拒绝回答紧急安全问题时的影响
4. **合规风险评估**：
   - 产品说明书信息的准确性是否满足消费者保护法要求
   - AI 生成内容是否需要明确标注
   - 错误操作指导的产品责任风险
5. **安全等级评定**：给出风险等级（高/中/低），并说明每个风险的可能后果
6. **合规建议**：上线前必须满足的安全合规条件

输出要求：
- 用中文回答
- 每个风险项标注风险等级（🔴高 🟡中 🟢低）
- 引用具体的失败用例作为证据
- 给出明确的"上线阻塞项"和"上线建议项"
""",
    },
    {
        "name": "产品经理",
        "emoji": "📊",
        "instructions": """\
你是一名产品经理，负责评估 AI 客服系统的用户体验和业务价值。你的任务是从**用户和业务**角度分析评测结果。

分析要求：
1. **用户体验评估**：
   - 用户最常问的问题类型（doc_extraction）表现如何？
   - 用户用口语/中文问问题（user_rewrite）时体验如何？
   - 回答的完整性和可用性如何？
2. **业务价值分析**：
   - 当前系统能替代多少人工客服工作量？
   - 哪些场景已经可以放心交给 AI？哪些必须人工兜底？
3. **竞品对标**：行业内类似 RAG 客服系统的通常表现水平
4. **上线策略建议**：
   - 灰度发布计划
   - 用户分群策略（新用户 vs 老用户）
   - 功能开关建议（哪些能力先开、哪些后开）
5. **成功指标定义**：上线后应该关注哪些业务指标
6. **用户信任建设**：如何让用户信任 AI 回答的准确性

输出要求：
- 用中文回答
- 站在用户视角思考，避免过于技术化
- 给出具体的上线里程碑和时间建议
- 包含风险预案
""",
    },
    {
        "name": "QA 测试专家",
        "emoji": "🧪",
        "instructions": """\
你是一名资深 QA 测试专家。你的任务是从**测试质量和覆盖度**角度分析评测结果和测试用例设计。

分析要求：
1. **测试覆盖度**：
   - 164 个用例是否足够覆盖 4 个产品线 × 4 种问题类型？
   - 是否存在测试盲区（某些产品/功能/场景未覆盖）？
   - 边界用例和异常场景的覆盖是否充分？
2. **测试用例质量**：
   - expected_answer 的设定是否合理？是否过于严格或宽松？
   - 问题类型的分布是否合理？
   - 是否存在重复或冗余的用例？
3. **评分体系评估**：
   - 四维评分（正确性、忠实度、相关性、引用）的权重是否合理？
   - Judge 模型（gpt-4o）的评分是否存在系统性偏差？
   - Claim Recall 的评估方式是否公平？
4. **失败模式分析**：
   - 失败用例是否存在共性模式？
   - 哪些失败是系统问题 vs 测试用例问题？
5. **质量门禁建议**：CI/CD 中应该设置什么样的质量阈值？
6. **测试改进建议**：下一轮测试应该补充哪些用例？

输出要求：
- 用中文回答
- 提供具体的用例补充建议（含问题示例）
- 给出质量门禁的具体阈值建议
- 区分"测试问题"和"系统问题"
""",
    },
    {
        "name": "实施顾问",
        "emoji": "🛠️",
        "instructions": """\
你是一名资深全栈工程师兼 RAG 系统实施顾问。你的任务是根据评测数据，给出**具体的、可直接执行的修改方案**。

你熟悉的项目技术栈和架构：
- 框架：OpenAI Agents SDK（Python），使用 Agent + Runner.run() 调用
- 流程：Triage Agent（语言检测/翻译/产品路由/查询扩写）→ Support Agent（产品专用 RAG）
- Triage 指令：rag_server/app/services/instructions/triage.md
- Support Agent 指令：rag_server/app/services/instructions/{master-ultra,futurist-ultra,aegis-ultra,aegis-edu,general}.md
- Vector Store：OpenAI 远程 Vector Store，按产品分库，另有一个 all-products 库
- 文档来源：src/content/pages/{product}/*.md（Markdown 格式）
- 评测脚本：rag_server/eval/run_eval.py
- 测试用例：rag_server/eval/test_cases.json

分析要求：

1. **Prompt 修改建议**：针对失败用例中暴露的问题，给出对 triage.md 或各产品 instructions 的具体修改建议
   - 写出需要修改的文件路径
   - 给出修改前后的对比（原文 → 建议改为）
   - 说明修改的理由和预期效果

2. **测试用例修正**：针对不合理的测试用例，给出具体的修正建议
   - 列出需要修正的用例 ID
   - 给出修正后的 question 和/或 expected_answer
   - 说明为什么当前的设定不合理

3. **Vector Store 优化**：
   - 是否需要调整文档分块策略？
   - 是否有文档内容本身需要补充或修改？
   - 是否需要为特定产品建立专用 Vector Store？

4. **代码改动建议**：针对 run_eval.py 或 chatkit_handler.py 中需要改动的地方
   - 给出文件路径和函数名
   - 描述需要改动的逻辑
   - 如果改动较小，直接给出代码片段

5. **优先级排序**：将所有建议按以下维度排序
   - 影响范围（影响多少个失败用例）
   - 实施难度（改一行 prompt vs 重构架构）
   - 风险等级（安全相关 > 准确性 > 体验）

输出要求：
- 用中文回答
- 每条建议必须包含：文件路径、具体改动内容、影响的用例 ID、预期效果
- 使用 markdown 代码块展示修改前后对比
- 按优先级从高到低排列
- 区分"立即执行"（< 1小时）、"短期"（1-3天）、"中期"（1-2周）三个时间档
""",
    },
]

DECISION_MAKER_INSTRUCTIONS = """\
你是一名综合决策者，负责汇总多位专家的分析意见，给出最终的上线决策建议。

你将收到以下专家的分析报告：
1. RAG 技术专家 — 技术架构和优化方向
2. 产品安全专家 — 安全风险和合规要求
3. 产品经理 — 用户体验和业务价值
4. QA 测试专家 — 测试质量和覆盖度
5. 实施顾问 — 具体可执行的修改方案

你的任务：
1. **识别共识**：各位专家一致认同的结论
2. **调和分歧**：如果专家意见存在冲突，给出你的判断
3. **最终决策**：明确给出"建议上线"/"有条件上线"/"不建议上线"
4. **行动计划**：按优先级排列的具体行动项，每项标注负责角色和预期时间
5. **风险接受声明**：如果建议上线，明确列出接受了哪些残余风险

输出要求：
- 用中文回答
- 决策必须明确，不能模棱两可
- 行动计划要具体到"谁在什么时间做什么"
- 最终输出一个简洁的 Go/No-Go 表格
"""


# ── 执行分析 ──────────────────────────────────────────────────────────────


async def run_expert_analysis(
    context: str, model: str,
) -> list[dict[str, str]]:
    """Run all expert agents in parallel and collect their analyses."""
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Phase 1: 专家并行分析")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    is_reasoning_model = model.startswith(("gpt-5", "o"))
    expert_settings = (
        ModelSettings(reasoning=Reasoning(effort="high"))
        if is_reasoning_model
        else ModelSettings(temperature=0.3)
    )

    async def run_one_expert(cfg: dict) -> dict[str, str]:
        agent = Agent(
            name=cfg["name"],
            instructions=cfg["instructions"],
            model=model,
            model_settings=expert_settings,
        )
        print(f"  {cfg['emoji']} {cfg['name']} 正在分析...")
        result = await Runner.run(agent, input=context)
        output = result.final_output
        text = output.strip() if isinstance(output, str) else str(output).strip()
        print(f"  {cfg['emoji']} {cfg['name']} 分析完成 ({len(text)} 字)")
        return {"name": cfg["name"], "emoji": cfg["emoji"], "analysis": text}

    expert_results = await asyncio.gather(
        *[run_one_expert(cfg) for cfg in EXPERT_CONFIGS]
    )
    return list(expert_results)


async def run_decision_maker(
    context: str, expert_results: list[dict[str, str]], model: str,
) -> str:
    """Run the decision maker agent with all expert analyses."""
    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Phase 2: 综合决策")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()

    combined_input = f"{context}\n\n---\n\n# 各专家分析报告\n\n"
    for er in expert_results:
        combined_input += f"## {er['emoji']} {er['name']}的分析\n\n{er['analysis']}\n\n---\n\n"

    decision_settings = (
        ModelSettings(reasoning=Reasoning(effort="high"))
        if model.startswith(("gpt-5", "o"))
        else ModelSettings(temperature=0.2)
    )
    agent = Agent(
        name="综合决策者",
        instructions=DECISION_MAKER_INSTRUCTIONS,
        model=model,
        model_settings=decision_settings,
    )
    print("  🎯 综合决策者正在汇总分析...")
    result = await Runner.run(agent, input=combined_input)
    output = result.final_output
    text = output.strip() if isinstance(output, str) else str(output).strip()
    print(f"  🎯 决策报告生成完成 ({len(text)} 字)")
    return text


def generate_report(
    expert_results: list[dict[str, str]],
    decision: str,
    report_path: Path,
    model: str,
) -> Path:
    """Generate the final markdown report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    sections = [
        f"# FF Robot RAG 评测多角色分析报告",
        "",
        f"> 生成时间：{now}  ",
        f"> 分析模型：{model}  ",
        f"> 专家数量：{len(expert_results)} 位 + 1 位决策者",
        "",
        "---",
        "",
    ]

    for er in expert_results:
        sections.extend([
            f"## {er['emoji']} {er['name']}",
            "",
            er["analysis"],
            "",
            "---",
            "",
        ])

    sections.extend([
        "## 🎯 综合决策",
        "",
        decision,
    ])

    content = "\n".join(sections)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    return report_path


# ── 主函数 ────────────────────────────────────────────────────────────────


async def main(
    report_path: Path,
    compare_path: Path | None,
    model: str,
):
    print()
    print("═══════════════════════════════════════════")
    print("  FF Robot RAG 多角色评测分析")
    print("═══════════════════════════════════════════")
    print(f"  报告: {report_path.name}")
    print(f"  模型: {model}")
    if compare_path:
        print(f"  对比: {compare_path.name}")
    print()

    report = load_report(report_path)
    compare_report = load_report(compare_path) if compare_path else None

    context = build_summary_context(report, compare_report)
    print(f"  数据上下文: {len(context)} 字")
    print()

    expert_results = await run_expert_analysis(context, model)

    decision = await run_decision_maker(context, expert_results, model)

    # Extract timestamp from report filename (e.g. report_20260318_012147.json → 20260318_012147)
    report_stem = report_path.stem  # "report_20260318_012147"
    report_ts = report_stem.replace("report_", "") if report_stem.startswith("report_") else report_stem
    answers_subdir = ANSWERS_DIR / report_ts
    output_path = answers_subdir / "expert_analysis.md"
    final_path = generate_report(expert_results, decision, output_path, model)

    print()
    print("═══════════════════════════════════════════")
    print(f"  ✅ 分析报告已生成: {final_path}")
    print("═══════════════════════════════════════════")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FF Robot RAG 评测多角色分析工具")
    parser.add_argument(
        "--report", type=str, default=None,
        help="评测报告路径（默认使用最新报告）",
    )
    parser.add_argument(
        "--compare", type=str, default=None,
        help="对比基准报告路径（可选）",
    )
    parser.add_argument(
        "--model", type=str, default=DEFAULT_MODEL,
        help=f"分析模型（默认: {DEFAULT_MODEL}）",
    )
    args = parser.parse_args()

    if args.report:
        rp = Path(args.report)
        if not rp.is_absolute():
            rp = EVAL_DIR / rp
    else:
        rp = find_latest_report()

    cp = None
    if args.compare:
        cp = Path(args.compare)
        if not cp.is_absolute():
            cp = EVAL_DIR / cp

    asyncio.run(main(report_path=rp, compare_path=cp, model=args.model))
