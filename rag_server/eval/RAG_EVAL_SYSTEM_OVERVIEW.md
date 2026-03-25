# FF Master RAG 评测系统设计文档

## 1. 系统概述

本评测系统用于系统性地衡量 FF Master 机器人用户手册 RAG（Retrieval-Augmented Generation）问答系统的质量。评测流程分为两个阶段：

1. **Phase 1 — RAG 查询**：将测试问题逐条发送给 RAG 系统（基于 OpenAI Assistants API），获取实际回答。
2. **Phase 2 — LLM 评分**：使用 Judge 模型（如 GPT-4o）对每条回答进行多维度打分和 Claim Recall 分析。

整体架构如下：

```
测试用例 (test_cases.json)
        │
        ▼
  Phase 1: 向 RAG 系统提问 → 收集实际回答
        │
        ▼
  Phase 2: Judge 模型评分 (质量评分 + Claim Recall)
        │
        ▼
  输出: 评测报告 (JSON + Markdown)
```

---

## 2. 测试用例设计

### 2.1 数据文件

测试用例存放在 `rag_server/eval/test_cases.json`，当前版本 v3.0.0，共 120 条。

每条用例的字段结构如下：

```json
{
  "id": 1,
  "category": "safety",
  "question_type": "doc_extraction",
  "question": "What safety distances are mentioned in the manual?",
  "expected_answer": "Two safety distances are specified: ...",
  "source_file": "safety-guidelines.md, safety-precautions.md"
}
```

| 字段 | 说明 |
| --- | --- |
| `id` | 唯一标识，1-120 |
| `category` | 内容分类（safety、specifications、battery 等 19 个类别） |
| `question_type` | 问题类型，四类之一（见下文） |
| `question` | 测试问题 |
| `expected_answer` | 期望的标准答案，用于 Judge 评分的参照 |
| `source_file` | 答案来源的 Markdown 文件（D 类题为 "N/A"） |

### 2.2 四类问题体系

我们将测试问题分为四个类型，模拟真实用户从"标准查询"到"边界挑战"的完整谱系：

| 类型 | 标识 | 数量 | 占比 | 目的 |
| --- | --- | --- | --- | --- |
| **A-文档抽取** | `doc_extraction` | 58 | 48.3% | 验证对手册明确事实的准确检索和复述 |
| **B-用户改写** | `user_rewrite` | 24 | 20.0% | 验证对口语化、模糊表述、错术语、中英混杂的鲁棒性 |
| **C-任务场景** | `task_scenario` | 21 | 17.5% | 验证多步骤任务、跨文档推理、条件判断的综合能力 |
| **D-不可答/风险** | `boundary_risk` | 17 | 14.2% | 验证对手册未覆盖内容和安全风险问题的正确拒答能力 |

**设计理念**：A 类是基线——如果连文档中的明确事实都答不好，后续优化无从谈起；B/C 类模拟真实用户行为——用户不会用标准术语提问，也常提出需要跨文档综合的复杂问题；D 类是护栏——确保系统不会在手册未覆盖的领域胡编乱造。

各类典型示例：

- **A 类**: "FF Master Ultra 有几个自由度？" — 标准术语、单一来源、明确答案
- **B 类**: "站不稳咋回事" — 口语化、省略主语、模糊表述
- **C 类**: "从开箱到第一次让机器人走路，完整步骤是什么" — 需综合 3+ 个文档
- **D 类**: "我听说这个机器人防水的，对吧" — 误导性前提，手册未提及防水

### 2.3 问题生成原则

详细的生成方法论记录在 `QUESTION_GENERATION_GUIDE.md` 中，核心原则如下：

1. **事实正确性优先**：expected_answer 中的每个数值、步骤必须可回溯到源文档
2. **避免贴原文**：期望答案是对原文的提炼总结，而非直接复制
3. **结构化表达**：多步骤答案使用编号列表，便于 Claim Recall 拆解
4. **适度信息量**：既不过于冗长，也要涵盖所有关键要点（claims）

---

## 3. 评分体系

### 3.1 五维度评分

每条回答由 Judge 模型在以下维度上打 0-10 分：

| 维度 | 权重 | 评估内容 | 评分锚点举例 |
| --- | --- | --- | --- |
| **Correctness** | 35% | 事实、数值、步骤是否正确 | 10=完全正确，5=部分正确部分错误，0=完全错误 |
| **Faithfulness** | 30% | 回答是否有手册依据，而非编造 | 10=每句话可溯源，3=大量编造，0=完全臆测 |
| **Relevance** | 20% | 回答是否聚焦问题、无跑题 | 10=直接简洁回答，5=部分跑题，0=完全无关 |
| **Citation** | 15% | 引用是否指向正确的源文件 | 10=引用正确，5=无引用但答案对，0=引用误导 |

**综合分** = Correctness×0.35 + Faithfulness×0.30 + Relevance×0.20 + Citation×0.15

分数门槛：
- **≥ 7 分**：通过（Pass）
- **5-7 分**：警告（Warning）
- **< 5 分**：失败（Fail）

### 3.2 Claim Recall（要点召回率）

借鉴 RAGAS 框架的 Claim Decomposition 方法：

1. 将 expected_answer 拆解为独立的原子事实（claims）
2. 逐条判断 RAG 的实际回答是否覆盖了该 claim
3. Claim Recall = 被覆盖的 claims 数 / 总 claims 数

**与五维度评分的关系**：
- Claim Recall 高 + Faithfulness 低 → 模型可能"猜对了"而非检索到
- Claim Recall 低 + Faithfulness 高 → 检索到了相关信息，但生成时遗漏了要点

### 3.3 错误分类标签

每条评分还会附带错误分类标签（Error Taxonomy），用于根因分析：

| 标签 | 含义 |
| --- | --- |
| `retrieval_miss` | 关键信息未被检索到 |
| `wrong_number` | 数值/参数错误 |
| `wrong_unit` | 单位错误 |
| `wrong_procedure` | 步骤/流程错误 |
| `unsupported_claim` | 回答中包含手册中不存在的声明 |
| `partial_answer` | 回答正确但严重不完整 |
| `over_refusal` | 手册有信息但系统拒绝回答 |
| `under_refusal` | 手册无信息但系统仍臆测回答 |
| `citation_wrong` | 引用指向错误文档 |
| `citation_missing` | 应有引用但缺失 |
| `irrelevant_content` | 包含大量无关内容 |

### 3.4 红线指标

用于 CI/CD 门禁的硬性指标，任一不通过即标记 FAIL：

| 红线 | 含义 | 默认阈值 |
| --- | --- | --- |
| 安全类严重错误 | 安全类问题的 Correctness < 3 | 0 次 |
| 拒答失败率 | D 类问题中系统未正确拒答的比例 | ≤ 5% |
| 规格精确率 | 规格类问题的 Correctness ≥ 7 的比例 | 可配置 |

---

## 4. 运行方式

评测脚本为 `rag_server/eval/run_eval.py`，支持多种运行模式：

```bash
cd rag_server

# 全量运行 120 条用例
python -m eval.run_eval

# 按 ID 运行指定用例
python -m eval.run_eval --ids 1 2 3

# 按内容分类筛选
python -m eval.run_eval --category safety

# 按问题类型筛选
python -m eval.run_eval --question-type user_rewrite

# 使用多个 Judge 模型对比
python -m eval.run_eval --judge-models gpt-4o gpt-4.1 o1

# 重复运行 N 次检测一致性
python -m eval.run_eval --repeat 3

# CI 门禁：通过率低于 80% 则返回非零退出码
python -m eval.run_eval --min-pass-rate 80
```

关键参数：

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--ids` | 运行指定 ID 的用例 | 全部 |
| `--category` | 按内容分类筛选 | 全部 |
| `--question-type` | 按问题类型筛选 | 全部 |
| `--judge-models` | 评分使用的 Judge 模型 | gpt-4o |
| `--concurrency` | 并发查询数 | 3 |
| `--repeat` | 重复运行次数（一致性测试） | 1 |
| `--min-pass-rate` | CI 门禁通过率阈值 (%) | 0（不启用） |
| `--max-query-time` | 慢查询阈值（秒） | 30 |

---

## 5. 输出文件说明

每次运行会产生三个输出文件，存放在带时间戳的目录中。以 `20260316_230305` 这次运行为例：

```
rag_server/eval/
├── reports/
│   └── report_20260316_230305.json    ← 完整评测报告（JSON）
├── answers/
│   └── 20260316_230305/
│       ├── eval_result.json            ← 逐条评测结果（JSON）
│       └── summary_report.md           ← 人类可读的总结报告（Markdown）
└── history.json                        ← 历次评测的趋势记录
```

### 5.1 summary_report.md — 总结报告

这是给人看的报告，包含以下板块：

**总体评分**：通过率、各维度平均分。以本次运行为例：

| 指标 | 得分 |
| --- | --- |
| 通过率 (≥7分) | **75.8%** (91/120) |
| 平均综合分 | **7.79/10** |
| 平均正确性 | 7.14/10 |
| 平均忠实度 | 8.54/10 |
| 平均相关性 | 8.66/10 |
| 平均引用质量 | 8.24/10 |

**Claim Recall**：

| 指标 | 值 |
| --- | --- |
| 平均 Claim Recall | **59.5%** |
| 全局 Claim Recall | **53.6%** (251/468 claims) |

**红线指标**：安全类零严重错误（PASS），拒答失败率 5.9%（FAIL，超出 5% 阈值），规格精确率 92.9%。

**按问题类型分布** — 这是评测的核心洞察之一：

| 问题类型 | 用例数 | 平均综合分 | 通过率 | Claim Recall |
| --- | --- | --- | --- | --- |
| A-文档抽取 | 58 | 8.9/10 | 91.4% | 80% |
| D-不可答/风险 | 17 | 8.15/10 | 82.4% | 41% |
| B-用户改写 | 24 | 6.73/10 | 54.2% | 44% |
| C-任务场景 | 21 | 5.62/10 | 52.4% | 34% |

可以看到 A 类和 D 类表现较好（通过率 > 80%），而 B 类和 C 类通过率仅约 50%，说明系统对口语化表述和多文档综合推理的能力有明显短板，这恰恰是四类问题体系设计的价值所在。

**错误分布**：列出所有错误类型及出现次数，便于定位系统弱点。本次最突出的错误是 `retrieval_miss`（34 次）和 `unsupported_claim`（25 次），说明检索遗漏和过度生成是当前的主要问题。

**失败用例详情**：列出所有综合分 < 5 的用例，标注分类、问题类型、错误标签和问题原文，方便逐条排查。

### 5.2 eval_result.json — 逐条评测结果

JSON 数组，每个元素对应一条测试用例的完整评测结果。以 Case #1 为例：

```json
{
  "id": 1,
  "category": "safety",
  "question_type": "doc_extraction",
  "question": "What safety distances are mentioned in the manual?",
  "source_file": "safety-guidelines.md, safety-precautions.md",
  "LLM_answer": "The FF Master robot manual specifies ...",
  "scores": {
    "correctness": 7,
    "faithfulness": 7,
    "relevance": 7,
    "citation": 7,
    "overall": 7.0,
    "comment": "回答中提到的两个主要安全距离与预期答案一致，但增加了..."
  },
  "error_tags": ["unsupported_claim", "irrelevant_content"],
  "claim_recall": {
    "score": 1.0,
    "supported_claims": 2,
    "total_claims": 2,
    "claims": [
      {
        "claim": "Maintain a safe distance of at least 50 cm ...",
        "verdict": 1
      },
      {
        "claim": "Reserve a safety area with a radius of at least 1 meter ...",
        "verdict": 1
      }
    ]
  },
  "query_time_s": 33.24
}
```

关键字段说明：

| 字段 | 说明 |
| --- | --- |
| `LLM_answer` | RAG 系统返回的实际回答原文 |
| `scores` | Judge 模型给出的四维度评分 + 综合分 + 中文评语 |
| `error_tags` | 错误分类标签列表（可能为空） |
| `claim_recall.claims` | 期望答案拆解后的每个 claim 及是否被覆盖 (verdict: 0/1) |
| `claim_recall.score` | 该条的 Claim Recall（0.0 ~ 1.0） |
| `query_time_s` | RAG 查询耗时（秒） |

### 5.3 report_20260316_230305.json — 完整评测报告

这是最完整的结构化报告，包含所有统计数据和逐条结果，适合程序化消费。顶层结构：

```json
{
  "meta": {
    "timestamp": "2026-03-16T15:14:46.274585+00:00",
    "assistant_id": "asst_V4jhdbF3IpYFzCo7aJ556Kbq",
    "judge_models": ["gpt-4o"],
    "primary_judge_model": "gpt-4o",
    "repeat_count": 1,
    "scoring_dimensions": ["correctness", "faithfulness", "relevance", "citation"],
    "weights": "correctness×0.35 + faithfulness×0.30 + relevance×0.20 + citation×0.15"
  },
  "summary": {
    "total_cases": 120,
    "pass_rate": "75.8%",
    "avg_overall": 7.79,
    "avg_claim_recall": 0.5946,
    "redline": { ... },
    "error_tag_distribution": { ... },
    "question_type_breakdown": { ... }
  },
  "category_breakdown": { ... },
  "question_type_breakdown": { ... },
  "results": [ ... ]
}
```

| 顶层 Key | 说明 |
| --- | --- |
| `meta` | 运行元信息：时间、模型、维度权重 |
| `summary` | 汇总统计：通过率、各维度平均分、红线指标、错误分布、问题类型分组 |
| `category_breakdown` | 按内容分类（safety、battery 等）的分组得分 |
| `question_type_breakdown` | 按问题类型（A/B/C/D）的分组得分和通过率 |
| `results` | 120 条完整的逐条评测结果（同 eval_result.json 的内容） |

### 5.4 history.json — 趋势追踪

每次运行的核心指标会追加到 `history.json`，用于观察系统质量随迭代的变化趋势。

---

## 6. 关键设计决策

### 为什么采用四类问题体系？

传统做法是只用文档中直接提取的 QA 对来评测，但这会严重高估系统能力。我们观察到：

- **A 类通过率 91.4%** — 文档原文问题，系统表现良好
- **B 类通过率 54.2%** — 用户换个说法就掉到一半
- **C 类通过率 52.4%** — 需要综合推理时更差

如果只用 A 类题，我们会得出"系统通过率 91%"的乐观结论，但真实用户体验远不如此。四类问题体系让我们看到系统的真实边界。

### 为什么同时用评分和 Claim Recall？

单纯的 0-10 评分是主观的，而 Claim Recall 提供了客观的覆盖率度量。两者结合能区分不同的失败模式——例如本次评测中 `joints` 类别平均分 10.0 且 Recall 95%（表现完美），而 `multi_hop` 类别平均分 5.38 且 Recall 仅 33%（严重不足）。

### 为什么需要错误分类标签？

知道"这条答错了"还不够，需要知道"为什么答错"。`retrieval_miss` 说明需要优化检索策略，`over_refusal` 说明 system prompt 过于保守，`unsupported_claim` 说明模型倾向于添加手册之外的内容。错误标签直接指向了优化方向。

---

## 7. 文件清单

```
rag_server/eval/
├── test_cases.json                 ← 120 条测试用例（四类问题）
├── run_eval.py                     ← 评测脚本（Phase 1 查询 + Phase 2 评分）
├── QUESTION_GENERATION_GUIDE.md    ← 问题生成方法论文档
├── RAG_EVAL_TECH_DOC.md            ← 评测技术文档
├── RAG_EVAL_SYSTEM_OVERVIEW.md     ← 本文档
├── history.json                    ← 历次评测趋势
├── reports/                        ← 完整报告 JSON
│   └── report_YYYYMMDD_HHMMSS.json
└── answers/                        ← 评测结果
    └── YYYYMMDD_HHMMSS/
        ├── eval_result.json        ← 逐条结果
        └── summary_report.md       ← 总结报告
```
