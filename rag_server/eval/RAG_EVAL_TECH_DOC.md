# FF Master RAG 评测方案技术文档 (V2)

## 1. 概述

### 1.1 背景

FF Master 系列人形机器人配备了基于 RAG（Retrieval-Augmented Generation，检索增强生成）的智能问答系统。为确保回答质量，我们搭建了一套自动化评测框架，从多维度量化评估系统表现，并提供错误归因分析和分层门禁机制。

### 1.2 评测目标

- 量化 RAG 系统的**正确性、忠实度和可靠性**
- 通过 **Claim Recall** 衡量回答对关键要点的覆盖率
- 通过**错误分类标签**快速定位问题根因
- 通过**红线指标**确保安全类、拒答类问题的底线质量
- 支持**多模型交叉验证**，减少评分偏差

---

## 2. 评测架构

### 2.1 整体流程

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────────────┐
│  测试用例集   │────▶│  RAG 系统 (Phase1) │────▶│   LLM 评分 (Phase2)    │
│ test_cases   │     │  OpenAI Assistant │     │ ┌─────────────────┐  │
│  .json       │     │  API (Streaming)  │     │ │ 质量评分 (4维度) │  │
└─────────────┘     └──────────────────┘     │ │ + error_tags    │  │
                                              │ ├─────────────────┤  │
                                              │ │ Claim Recall    │  │
                                              │ │ (RAGAS 方法)     │  │
                                              │ └─────────────────┘  │
                                              └──────────┬──────────┘
                                                         │
                                              ┌──────────▼──────────┐
                                              │   评测输出           │
                                              │ eval_result.json    │
                                              │ summary_report.md   │
                                              └─────────────────────┘
```

### 2.2 两阶段分离设计

| 阶段 | 说明 | 特点 |
| --- | --- | --- |
| **Phase 1: RAG 查询** | 将测试问题发送给 RAG 系统，收集回答 | 每个问题只查询一次，控制并发数 |
| **Phase 2: LLM 评分** | 用 Judge 模型对每个回答进行质量评分 + Claim Recall 分析 | 可用多模型并行评分；评分和 Recall 通过 asyncio.gather 并行执行 |

分离的好处：RAG 查询成本固定（只跑一次），可用多个 Judge 模型交叉验证。

---

## 3. 评分体系

### 3.1 质量评分（4 维度）

相比 V1 的 5 维度，V2 做了以下调整：
- **合并** Accuracy + Hallucination → Correctness + Faithfulness（消除重叠惩罚）
- **去除** Completeness（由 Claim Recall 结构化承担，避免双重衡量）

| 维度 | 权重 | 说明 | 校准锚点 |
| --- | --- | --- | --- |
| **Correctness（正确性）** | 35% | 事实、数值、步骤是否正确 | 10=全对；7=核心对，细节略偏；5=半对半错；3=重大错误；0=完全错 |
| **Faithfulness（忠实度）** | 30% | 回答是否基于检索证据，而非凭空编造 | 10=每句可溯源；7=基本有据；5=有据+有编；3=大量编造；0=全编 |
| **Relevance（相关性）** | 20% | 是否聚焦问题，无跑题 | 10=精准简洁；7=基本相关；5=部分跑题；0=完全无关 |
| **Citation（引用质量）** | 15% | 来源引用是否正确 | 10=正确引用；7=引用存在但部分错；5=无引用但答对；0=错误引用 |

**综合分** = Correctness×0.35 + Faithfulness×0.30 + Relevance×0.20 + Citation×0.15

**通过标准**：≥ 7 通过，5-7 警告，< 5 失败。

> **与 V1 的关键区别**：
> - Correctness 只扣"答错了"的分，不因"没答到"而扣分（那是 Claim Recall 的职责）
> - Faithfulness 专门衡量"有没有编"，和 Correctness 的"对不对"职责清晰分离
> - 对于手册未覆盖的问题（negative 类），正确拒答给 Faithfulness 10 分

### 3.2 Claim Recall（要点召回率）

参照 **RAGAS** 框架的 LLM-based Context Recall 方法：

1. 将期望答案拆解为若干**独立 claims**（原子级事实声明）
2. 逐条检查每个 claim 是否被 RAG 实际回答所覆盖
3. 计算：

$$
\text{Claim Recall} = \frac{\text{被覆盖的 claims 数}}{\text{总 claims 数}}
$$

**两种统计口径**：

| 指标 | 计算方式 | 说明 |
| --- | --- | --- |
| 平均 Claim Recall | 每个用例的 recall 取平均 | 反映单题平均覆盖表现 |
| 全局 Claim Recall | 全部 supported / 全部 total claims | 消除用例长短差异 |

> **重要说明**：Claim Recall 衡量的是**最终回答**对期望要点的覆盖率，而非**检索层**的 Evidence Recall。
> 区分诊断：
> - Claim Recall 高 + Faithfulness 低 → 模型可能凭常识猜对，不是检索好
> - Claim Recall 低 + Faithfulness 高 → 检索到了但生成时遗漏
> - 两者都低 → 检索有问题

### 3.3 错误分类标签（Error Taxonomy）

每条评分结果附带结构化错误标签，支持根因分析：

| 标签 | 含义 |
| --- | --- |
| `retrieval_miss` | 关键信息未被检索到 |
| `wrong_number` | 数值/参数错误 |
| `wrong_unit` | 单位错误 |
| `wrong_procedure` | 步骤/流程错误 |
| `unsupported_claim` | 包含手册中不存在的声明 |
| `partial_answer` | 回答正确但严重不完整 |
| `over_refusal` | 手册有信息但拒绝回答 |
| `under_refusal` | 手册无信息但仍臆测回答 |
| `citation_wrong` | 引用指向错误文档 |
| `citation_missing` | 应有引用但缺失 |
| `irrelevant_content` | 包含大量无关内容 |

**诊断价值**：可直接统计"失败用例中 38% 是 wrong_number，22% 是 retrieval_miss"，比只看均分更可操作。

---

## 4. 红线指标（Release Gate）

除整体通过率外，V2 新增了三条**红线指标**，作为 CI/CD 发布门禁：

| 红线 | 默认阈值 | 说明 |
| --- | --- | --- |
| **安全类严重错误** | = 0 | Safety 类用例中 Correctness < 3 的个数，必须为 0 |
| **拒答失败率** | ≤ 5% | Negative 类用例中被标记为 `under_refusal` 的比例 |
| **规格精确率** | 可配置 | Specifications 类用例中 Correctness ≥ 7 的比例 |

**CI 命令示例**：

```bash
python -m eval.run_eval \
  --min-pass-rate 80 \
  --safety-max-fails 0 \
  --negative-max-unsafe-pct 5 \
  --spec-min-exactness 90
```

任一红线不达标，脚本 exit 1。

---

## 5. 多模型交叉验证

### 5.1 支持的 Judge 模型

| 模型 | 特点 |
| --- | --- |
| **gpt-4o** | 基准评分模型，速度快，评分偏严格 |
| **gpt-4.1** | 较新模型，评分更细腻，偏宽松 |
| **o1** | 推理型模型，评判深入但速度慢（不支持 temperature） |

### 5.2 V1 基线测试结果参考

| 指标 | gpt-4o | gpt-4.1 | o1 |
| --- | --- | --- | --- |
| 通过率 | 17.3% | 32.0% | 20.0% |
| 平均综合分 | 3.85 | 5.34 | 4.35 |

三个模型**趋势一致**：规格参数类最差，negative/maintenance 最好，说明结论可靠。

---

## 6. 测试用例设计

### 6.1 规模与分类

- **75 个测试用例**，覆盖 **19 个分类**，涉及全部 25 个源文件
- 用例类型：事实型、对比型、多跳推理、否定型、口语化、中英双语

### 6.2 分类明细

| 分类 | 数量 | 说明 |
| --- | --- | --- |
| safety | 7 | 安全距离、急停、操作条件 |
| specifications | 9 | 规格参数（自由度、重量、速度等） |
| chinese | 6 | 中文问答 |
| negative | 5 | 手册未覆盖的话题，测试拒答能力 |
| remote_control | 5 | 遥控器操作和模式切换 |
| startup / shutdown | 4+4 | 开机/关机流程 |
| interaction | 4 | 语音交互、唤醒词、定制化 |
| multi_hop | 4 | 跨文档综合推理 |
| fuzzy | 4 | 口语化/模糊表达 |
| battery / charging | 3+3 | 电池和充电 |
| computational / joints / sensors | 3+3+2 | 硬件配置 |
| product_comparison | 3 | 版本差异对比 |
| app / hardware_interface / maintenance | 2+2+2 | 其他 |

---

## 7. 输出产物

每次评测自动生成：

```
eval/answers/{YYYYMMDD_HHMMSS}/
  eval_result.json              ← 每条用例结果 + 评分 + claim_recall + error_tags
  summary_report.md             ← 可读报告（总分 / 红线 / 错误分布 / 分类 / 失败列表）
eval/reports/report_{ts}.json   ← 完整原始数据
eval/history.json               ← 历史趋势
```

### 7.1 eval_result.json 结构

```json
{
  "id": 1,
  "category": "safety",
  "question": "...",
  "source_file": "safety-guidelines.md",
  "LLM_answer": "（RAG 回答）",
  "scores": {
    "correctness": 8, "faithfulness": 9, "relevance": 9, "citation": 5,
    "overall": 7.8, "comment": "..."
  },
  "error_tags": ["citation_missing"],
  "claim_recall": {
    "score": 0.67,
    "supported_claims": 2, "total_claims": 3,
    "claims": [
      {"claim": "安全距离至少 50cm", "verdict": 1},
      {"claim": "安全区域半径至少 1 米", "verdict": 1},
      {"claim": "不允许人员站立", "verdict": 0}
    ]
  }
}
```

### 7.2 summary_report.md 内容

1. 总体评分（4 维度 + 综合分）
2. Claim Recall（平均 + 全局）
3. 红线指标状态（PASS/FAIL）
4. 错误分布统计表
5. 分类明细（综合分 + Recall）
6. 性能指标
7. 多模型对比（如适用）
8. 失败用例列表（含错误标签）

---

## 8. 使用方式

```bash
cd rag_server

# 基础用法
python -m eval.run_eval

# 多模型评分
python -m eval.run_eval --judge-models gpt-4o gpt-4.1 o1

# 一致性测试
python -m eval.run_eval --repeat 3

# CI/CD 门禁（红线 + 通过率）
python -m eval.run_eval \
  --min-pass-rate 80 \
  --safety-max-fails 0 \
  --negative-max-unsafe-pct 5 \
  --spec-min-exactness 90
```

---

## 9. V1 → V2 变更对照

| 项目 | V1 | V2 |
| --- | --- | --- |
| 评分维度 | 5 个（Accuracy, Completeness, Relevance, Hallucination, Citation） | 4 个（Correctness, Faithfulness, Relevance, Citation） |
| 维度重叠 | Accuracy/Hallucination 重叠；Completeness/Recall 重叠 | 职责清晰分离，无重叠 |
| 召回率名称 | Context Recall（名称不准确） | Claim Recall（明确指最终回答覆盖率） |
| 校准锚点 | 无 | 每个维度有 0/3/5/7/10 明确定义 |
| 错误归因 | 仅 comment 文本 | 结构化 error_tags（11 种标签） |
| 红线指标 | 无 | 安全严重错误 / 拒答失败率 / 规格精确率 |
| CI 门禁 | 仅 --min-pass-rate | 通过率 + 3 条红线 |
| Judge prompt | 通用 | 带校准锚点，避免重叠惩罚 |

---

## 10. 当前局限与后续计划

### 10.1 已知局限

| 局限 | 说明 |
| --- | --- |
| **无 Evidence Recall** | Assistants API 不暴露检索的 chunks，无法单独测量检索层召回率 |
| **无规则化评分** | 数值/按键/步骤类问题仍依赖 LLM Judge，不如精确匹配稳定 |
| **数据集规模** | 75 条 / 19 类，部分类仅 2-3 条，统计波动较大 |
| **gold_evidence 未标注** | test_cases 仅有 source_file，未细化到 chunk/section 级 |

### 10.2 优先优化方向

| 优先级 | 方向 | 说明 |
| --- | --- | --- |
| P0 | 接入检索日志 | 改造 RAG 接口，记录 retrieved chunks + scores，实现真正的 Evidence Recall@K |
| P1 | 规则化评分 | 对数值、按键组合、步骤顺序加精确匹配，减少 LLM 评分波动 |
| P1 | gold_evidence 标注 | 将 source_file 升级为 chunk 级证据标注 |
| P2 | 数据集分层 | 拆为 Core Set（CI 门禁）+ Regression Set（趋势对比）+ Challenge Set（压力测试） |
| P2 | 多轮对话测试 | 评估上下文记忆和追问能力 |
| P3 | Judge 校准验证 | 准备 20 条人工标定样例，量化不同 Judge 模型的偏差系数 |
