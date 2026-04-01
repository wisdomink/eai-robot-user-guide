# FF Robot 智能问答系统 — 技术创新点挖掘清单

> 生成时间：2026-04-01  
> 项目：EAI Robot User Guide (H5) — 全栈 AI 问答 + 语义搜索系统  
> 分析范围：后端多 Agent 工作流、前端混合搜索、流式事件重写、智能告警、动态推荐引擎

---

## 一、挖掘清单总览

| 编号 | 技术方案名称 | 类别 | 授权前景 |
|------|-------------|------|---------|
| P-01 | 基于分层多 Agent 路由的产品线智能问答方法 | 算法与逻辑改进 | ⭐⭐⭐ 高 |
| P-02 | SSE 流式事件中图片 URL 重写与引用坐标自适应修正方法 | 系统架构与流程 | ⭐⭐⭐ 高 |
| P-03 | 文件引用到 SPA 可导航实体的实时流式转换方法 | 交互与用户体验 | ⭐⭐⭐ 高 |
| P-04 | 精确搜索与语义搜索双通道融合的混合检索方法 | 算法与逻辑改进 | ⭐⭐☆ 中高 |
| P-05 | 基于规则分类引擎的智能告警分级处理方法 | 系统架构与流程 | ⭐⭐☆ 中高 |
| P-06 | 对话内动态推荐引擎与购买意图感知方法 | 算法与逻辑改进 | ⭐⭐ 中 |
| P-07 | 跨语言查询扩写驱动的 RAG 检索优化方法 | 算法与逻辑改进 | ⭐⭐ 中 |
| P-08 | 多维度 RAG 质量自动化评测框架 | 系统架构与流程 | ⭐☆ 中低 |

---

## 二、方案深度拆解

---

### P-01：基于分层多 Agent 路由的产品线智能问答方法

**【解决的技术问题】**

在多产品线（人形/轮式/四足/教育版机器人 + 车辆）的技术支持场景中，传统单一 RAG 系统存在以下缺陷：
1. **检索精度低**：所有产品文档混合存储在单一向量库中，跨产品术语干扰严重（如"充电"在不同产品中步骤完全不同）；
2. **语言适配差**：用户可能使用中文或英文提问，文档以英文为主，直接检索中文查询召回率极低；
3. **无法有效拦截超范围问题**：用户可能询问股票、天气等无关话题，系统缺乏统一的范围守卫机制。

**【核心技术特征】**

采用两阶段 Agent 架构（Triage → Support）：

1. **Triage Agent（路由预处理器）** — [`chatkit_handler.py:181-196`](rag_server/app/services/chatkit_handler.py:181)
   - 结构化输出：通过 Pydantic `TriageOutput` 模型强制 JSON schema（`input_lang`, `query_scope`, `query_type`, `query_text`, `purchase_intent`, `recommendation_hit`）
   - 指令模板动态注入：`{{recommendation_rules}}` 和 `{{purchase_intent_rules}}` 在运行时由 `RecommendationEngine.build_triage_rules_prompt()` 生成
   - 6 步流水线：语言检测 → 范围识别 → 产品识别 → 查询扩写 → 购买意图识别 → 推荐规则匹配
   - 前缀拦截机制：预定义 prompt 直接短路路由，避免 LLM 推理延迟

2. **Support Agent 路由矩阵** — [`chatkit_handler.py:198-234`](rag_server/app/services/chatkit_handler.py:198)
   - 7 个独立 Support Agent，各自绑定专属 Vector Store ID
   - `out-of-scope` Agent 无 file_search 工具，以 `_NO_TOOL_MODEL_SETTINGS` 运行
   - 指令模板预加载 `_INSTRUCTION_TEMPLATES`，避免运行时磁盘 I/O

3. **查询替换注入** — [`chatkit_handler.py:698-702`](rag_server/app/services/chatkit_handler.py:698)
   - 在 conversation history 中定位最后一条 `role=user` 消息，替换为 Triage 扩写后的 `query_text`
   - 确保 Support Agent 的 file_search 使用优化后的英文查询，而非用户原始输入

4. **Agent 追踪链** — [`chatkit_handler.py:668-696`](rag_server/app/services/chatkit_handler.py:668)
   - 每轮对话记录完整的 Triage → Support 决策链（`agent_traces`），包含路由依据、向量库 ID、工具列表

**【创新性分析】**

| 对比项 | 通用开源方案（LangChain/LlamaIndex） | 本方案 |
|--------|--------------------------------------|--------|
| Agent 路由 | 基于 LLM function calling 或 tool selection | 专用 Triage Agent 输出结构化 JSON，强类型约束 |
| 知识库隔离 | 通常单一向量库 + metadata filter | 每产品独立 Vector Store，物理隔离，无交叉干扰 |
| 查询优化 | 用户原始 query 直接检索 | Triage 层完成跨语言翻译+领域术语扩写后再检索 |
| 超范围防护 | 通常后置过滤或无 | 前置 Triage 二分法（`query_scope`）+ 独立 out-of-scope Agent |
| 前缀短路 | 无 | 预定义 prefix 直接输出固定路由，零 LLM 推理开销 |

---

### P-02：SSE 流式事件中图片 URL 重写与引用坐标自适应修正方法

**【解决的技术问题】**

当 AI 回答通过 ChatKit 协议在 iframe（CDN 域名 cdn.platform.openai.com）中渲染时：
1. 回答中的相对路径图片（`/images/docx/xxx.png`）无法解析，导致图片不显示；
2. 图片 URL 重写后文本长度改变，原始 `file_citation` 的字符位置索引错位，引用标记显示在错误的位置。

**【核心技术特征】**

`_EventStreamRewriter` 类 — [`chatkit_handler.py:105-147`](rag_server/app/services/chatkit_handler.py:105)

1. **有状态文本缓冲区**：维护 `_text_buf: dict[tuple[str, int], str]`，以 `(item_id, content_index)` 为键，逐 delta 累积原始文本
2. **双模式 URL 重写**：正则匹配 Markdown 图片语法 `![alt](/images/...)` 和 HTML img 标签 `<img src="/images/...">`
3. **引用坐标修正算法** — [`_compute_rewrite_offset()`](rag_server/app/services/chatkit_handler.py:92)
   - 遍历原始文本中所有图片匹配项
   - 统计 annotation.index 之前有多少个 URL 被前缀扩展
   - 将 annotation.index 增加 `count × len(PUBLIC_BASE_URL)` 个偏移量
4. **三种事件类型处理**：
   - `thread.item.added` / `thread.item.done`：完整内容重写
   - `thread.item.updated`：增量 delta 重写 + annotation 坐标修正

**【创新性分析】**

这是一个专门针对"流式 AI 回答中图文混排场景"的技术问题。现有开源社区中：
- ChatKit/Vercel AI SDK 等均不处理 iframe 跨域图片问题
- 没有已知的开源实现处理"流式 delta 累积 → URL 重写 → 引用坐标同步修正"这一链路
- 坐标修正算法的核心思想（基于原始文本而非重写后文本计算偏移）是反直觉的，构成非显而易见的技术方案

---

### P-03：文件引用到 SPA 可导航实体的实时流式转换方法

**【解决的技术问题】**

RAG 系统检索文档后，LLM 回答中的 `file_citation` 引用仅包含文件名（如 `master-ultra-charging.md`），无法直接映射为前端 SPA 的路由路径。现有方案要么不提供引用链接，要么生成全页面跳转（打断用户体验）。

**【核心技术特征】**

1. **文件→路由映射表构建** — [`_build_file_slug_map()`](rag_server/app/services/chatkit_handler.py:270)
   - 解析 `sidebar.json`，建立双重索引：`{relative_path: {slug, title}}` + `{basename: {slug, title}}`
   - 双重索引兼容 OpenAI API 返回相对路径或仅文件名两种情况

2. **自定义 ResponseStreamConverter** — [`FFRobotConverter`](rag_server/app/services/chatkit_handler.py:306)
   - 覆写 `file_citation_to_annotation()` 方法
   - 将 `file_citation` 转换为 `EntitySource`（带 `data.slug` 字段和 `interactive=True`）
   - 产出 `Annotation` 对象嵌入 SSE 流

3. **前端实体点击拦截** — [`ChatPanel.tsx:183-195`](src/components/chat/ChatPanel.tsx:183)
   - `entities.onClick` handler 从 `entity.data.slug` 构造 URL
   - 调用 `onEntityNavigate` → React Router `navigate()` 执行 SPA 内部跳转
   - 支持 hash anchor 定位（延迟 300ms 等待渲染后 scrollIntoView）

**【创新性分析】**

这构成了一条完整的 **"RAG 引用 → SPA 导航"** 端到端链路：
- **后端**：file_citation → sidebar.json 映射 → EntitySource（携带 slug）
- **前端**：EntitySource → click handler → React Router navigate

现有 RAG 框架（LangChain、LlamaIndex）的引用处理止步于"显示来源文件名"，不涉及 SPA 路由映射。本方案的"双重索引 + 流式转换 + 前端拦截"三层架构是独特的。

---

### P-04：精确搜索与语义搜索双通道融合的混合检索方法

**【解决的技术问题】**

纯语义搜索存在延迟（需要后端 API 调用），纯精确搜索缺乏语义理解能力。用户在搜索框输入时需要"即时反馈 + 深度理解"兼得。

**【核心技术特征】**

1. **双通道架构** — [`useSearch.ts`](src/hooks/useSearch.ts)
   - **精确通道**（零延迟）：`searchExact()` 基于构建时预生成的 `ContentChunk[]` 缓存，三级打分（标题匹配 100 分 / Section 标题 50 分 / 正文 10 分）
   - **语义通道**（400ms debounce）：`useSemanticSearch()` 调用后端 `/api/search` → OpenAI Vector Store Search API

2. **内容预分块** — [`chunks.ts`](src/content/chunks.ts)
   - 在构建时按 `## ` 标题分割所有 Markdown 页面
   - 生成 `ContentChunk`（含 pageSlug, headingAnchor, textPreview）
   - 过滤 < 20 字符的碎片段

3. **智能去重合并** — [`useSearch.ts:143-160`](src/hooks/useSearch.ts:143)
   - 以语义结果为优先，精确结果按 `slug#headingAnchor` 去重
   - 处理"语义结果无 anchor（页面级匹配）时覆盖该页面所有精确段落结果"的边界情况

4. **跨通道导航** — [`navigateToResult()`](src/hooks/useSearch.ts:163)
   - 语义结果额外传递 `highlight-section` 参数，在目标页面高亮对应段落
   - 精确结果传递 `q` 参数，触发页内关键词高亮 + 前后导航

**【创新性分析】**

| 对比项 | 通用方案（Algolia / ElasticSearch） | 本方案 |
|--------|-------------------------------------|--------|
| 精确搜索 | 服务端全文索引 | 客户端构建时预计算，零网络延迟 |
| 语义搜索 | 需要额外配置 embedding | 复用 RAG 的 Vector Store API |
| 结果融合 | 简单拼接或 RRF | 基于 anchor 粒度的智能去重 |
| 用户体验 | 两种搜索独立 | 同一搜索框，精确结果即时显示，语义结果 400ms 后追加替换 |

---

### P-05：基于规则分类引擎的智能告警分级处理方法

**【解决的技术问题】**

AI 系统的 ERROR 日志中，大量为已知无害错误（如启动预热失败、客户端断开），若全部发送告警邮件会造成"告警疲劳"。现有方案要么全报要么全不报。

**【核心技术特征】**

`SmartAlertHandler` — [`alert_handler.py`](rag_server/app/core/alert_handler.py)

1. **四级分类引擎**：
   - `alert`：立即发送（认证失败、服务不可达、Agent 崩溃、OOM）
   - `burst`：滑动窗口检测重复出现 N 次后才告警（OpenAI 超时、文件搜索失败）
   - `suppress`：静默忽略（启动预热、客户端断开、AbortError）
   - `digest`：周期性汇总发送（默认兜底）

2. **规则引擎** — [`AlertRule` dataclass](rag_server/app/core/alert_handler.py:57)
   - 正则匹配 `{logger_name}: {message}`
   - 首匹配原则（top-to-bottom, first match wins）
   - 运行时编译缓存

3. **滑动窗口 + 冷却机制**：
   - `_burst_windows: dict[fingerprint, deque[timestamp]]`
   - 窗口内计数达阈值 → 检查冷却期 → 发送并清空
   - 指纹算法：`hashlib.md5(f"{logger_name}:{normalized_message}")`

4. **上下文感知邮件**：
   - 环形缓冲区 `_context_buffer` 保留最近 N 条日志
   - 告警邮件包含触发日志前后的上下文记录

5. **周期性摘要**：
   - 守护线程定时器 `_flush_digest()` 每小时（可配置）汇总发送

**【创新性分析】**

通用日志告警方案（PagerDuty、Sentry、CloudWatch Alarms）是外部 SaaS，需要额外集成且无法针对 AI Agent 场景深度定制。本方案作为 Python logging Handler 的子类内嵌于应用中，具备：
- 零外部依赖的自包含告警能力
- 针对 AI Agent 场景的预置规则（OpenAI API 超时、模型幻觉错误等）
- Burst + Digest 双缓冲降噪机制

---

### P-06：对话内动态推荐引擎与购买意图感知方法

**【解决的技术问题】**

在用户与 AI 问答交互过程中，如何在不打断对话流的前提下，精准识别购买意图并推送相关产品推荐或留资表单。

**【核心技术特征】**

1. **三阶段流水线** — [`FFRobotChatKitServer.respond()`](rag_server/app/services/chatkit_handler.py:577)
   - Phase 1：Triage 输出 `purchase_intent` + `recommendation_rule_id`
   - Phase 2：Support Agent 正常回答（流式）
   - Phase 3：回答完成后，`RecommendationEngine.evaluate_post_answer()` 决定是否追加 Widget

2. **推荐去重机制** — [`RecommendationEngine._shown`](rag_server/app/services/recommendation_engine.py:199)
   - `dict[thread_id, list[shown_rule_id]]`
   - 每种推荐在同一 thread 中仅展示一次
   - 优先级：catalog rule > purchase-intent lead capture

3. **动态规则注入** — [`build_triage_rules_prompt()`](rag_server/app/services/recommendation_engine.py:99)
   - 从 DynamoDB/本地 JSON 读取运营配置的推荐规则
   - 编译为紧凑的 prompt 片段注入 Triage Agent 指令
   - 支持运营人员通过管理界面实时增删规则，无需重启服务

4. **留资表单 Widget** — [`_build_lead_card()`](rag_server/app/services/chatkit_handler.py:483)
   - 通过 ChatKit Widget（Card + Select + Input）在对话流中内嵌表单
   - 表单提交通过 `ActionConfig(handler="server")` 路由到后端 `action()` 方法
   - 双语适配（`is_cn` 决定标签和 placeholder）

**【创新性分析】**

现有 AI 客服方案中，推荐/留资通常是独立模块（弹窗、侧边栏），与对话流脱节。本方案实现了"对话即推荐"的无缝体验：Triage Agent 在路由阶段就完成了意图识别，推荐卡片作为流式事件附加在 AI 回答之后，用户无需切换界面。

---

### P-07：跨语言查询扩写驱动的 RAG 检索优化方法

**【解决的技术问题】**

用户以中文提问、文档以英文存储时，直接使用原始中文 query 检索英文向量库的召回率极低。

**【核心技术特征】**

1. **Triage Agent Step 4** — [`instructions/triage.md:81-96`](rag_server/app/services/instructions/triage.md:81)
   - 中文输入 → 英文翻译 + 同义词/术语扩展
   - 保持简洁（不超过 3 句话），避免过度扩展导致检索噪声
   - 扩写结果直接作为 Support Agent 的 file_search 查询

2. **对话历史注入** — [`chatkit_handler.py:698-702`](rag_server/app/services/chatkit_handler.py:698)
   - 不是简单地在对话末尾追加扩写 query
   - 而是**替换**最后一条用户消息为 `triage_output.query_text`
   - 确保 Support Agent 的 context 中用户消息已是优化后的英文查询

**【创新性分析】**

LangChain 的 query transformation（HyDE、Multi-Query）是通用方案。本方案的特色在于：
- 翻译 + 扩写在同一个 Triage Agent 调用中完成（单次 LLM 推理）
- 扩写受领域约束（"不要加入无关发挥"、"不要把其他产品名称写进 query_text"）
- 通过对话历史替换（而非追加）确保 Support Agent 的行为一致性

---

### P-08：多维度 RAG 质量自动化评测框架

**【解决的技术问题】**

RAG 系统上线后如何持续监控回答质量，确保模型升级、prompt 修改、文档更新不引入回归。

**【核心技术特征】**

[`eval/run_eval.py`](rag_server/eval/run_eval.py)

1. **端到端评测**：复用生产 Triage → Support 管线，非隔离测试
2. **五维评分**：Correctness, Faithfulness, Relevance, Citation, Claim Recall
3. **多 Judge 对比**：支持同时使用多个 LLM（gpt-4o, o1 等）作为评判者
4. **Claim Recall**：从 expected_answer 提取关键声明，逐条检验是否被 AI 回答覆盖
5. **一致性测试**：`--repeat N` 多次运行，计算标准差，识别不稳定用例
6. **CI 门禁**：`--min-pass-rate 80` 可集成到 CI/CD 管线

**【创新性分析】**

RAGAS、TruLens 等开源评测框架提供通用能力，但本方案针对多产品 RAG 的特殊需求做了深度定制：
- 164 个分 4 类问题的测试集（doc_extraction / user_rewrite / task_scenario / boundary_risk）
- 端到端走通 Triage 路由而非单 Agent 测试
- 一致性分析是该框架的独特功能

---

## 三、模拟查重与通过率预估

### 评估标准

根据 CNIPA（中国国家知识产权局）和 CIPO 审查习惯：
- **新颖性**：是否有相同技术方案的现有技术
- **创造性**：是否对本领域技术人员"非显而易见"
- **实用性**：是否能在产业上应用并产生技术效果

### 授权前景评估

| 编号 | 方案 | 新颖性 | 创造性 | 推荐度 | 说明 |
|------|------|--------|--------|--------|------|
| **P-01** | 分层多 Agent 路由 | 高 | 中高 | ⭐⭐⭐ **强烈推荐** | 核心专利。"结构化 Triage → 产品隔离 Vector Store → 查询替换注入"三位一体的架构具有系统性创新。与 LangChain/LlamaIndex 的 Agent 路由方案有本质区别。建议以方法+系统双独权撰写。 |
| **P-02** | 流式 URL 重写 + 坐标修正 | 高 | 高 | ⭐⭐⭐ **强烈推荐** | 这是最具专利性的点。"流式 delta 累积 → URL 重写 → annotation 坐标偏移同步修正"的技术方案在已知文献中未见相同记载。解决的问题具体（iframe 跨域图片 + 引用错位），方案巧妙（基于原始文本计算偏移而非重写后文本）。 |
| **P-03** | 文件引用→SPA 实体转换 | 中高 | 中高 | ⭐⭐⭐ **推荐** | "RAG file_citation → sidebar 双重索引 → EntitySource → 前端 SPA navigate"端到端链路。可与 P-02 合并为一个专利（流式回答中引用处理与导航方法）以增强系统性。 |
| **P-04** | 混合检索双通道融合 | 中 | 中 | ⭐⭐ **可选** | 精确+语义混合搜索本身并非全新概念，但"客户端构建时预分块 + 零延迟精确搜索 + 后端语义搜索 400ms 追加"的用户体验方案有一定创造性。建议作为从属权利要求或防御性专利。 |
| **P-05** | 智能告警分级引擎 | 中 | 中高 | ⭐⭐ **可选** | 四级分类（alert/burst/suppress/digest）+ 指纹去重 + 滑动窗口 + 上下文邮件的组合方案有技术含量，但告警分级本身在运维领域有大量现有技术。建议聚焦"AI Agent 场景下的告警降噪"角度撰写。 |
| **P-06** | 对话内动态推荐引擎 | 中 | 中 | ⭐ **备选** | 推荐引擎本身不新，但"Triage Agent 前置意图识别 + 流式回答后追加 Widget + 运营动态配置"的组合有一定新意。建议与 P-01 合并论述。 |
| **P-07** | 跨语言查询扩写 | 低 | 低 | ❌ 不建议独立申请 | 查询扩写/翻译在 RAG 领域是成熟技术（HyDE, Multi-Query），建议作为 P-01 的从属权利要求。 |
| **P-08** | RAG 评测框架 | 低 | 低 | ❌ 不建议独立申请 | RAGAS/TruLens/DeepEval 等开源框架覆盖了核心功能。可在 P-01 中作为"质量保障方法"的从属权利要求。 |

---

## 四、TOP 5 推荐申请清单

### 🏆 Case 1：P-02 + P-03 合并 — 流式 AI 回答中的引用处理与多媒体内容自适应方法

**专利主题**：一种在 SSE 流式 AI 对话中实现图片 URL 域适配与引用坐标同步修正的方法

**独权方向**：
1. 维护有状态文本缓冲区，逐 delta 累积原始文本
2. 检测并重写图片 URL 为绝对路径
3. 基于重写前的原始文本计算每个 annotation 的坐标偏移量
4. 将文件引用转换为携带 SPA 路由信息的可交互实体
5. 前端通过实体点击事件执行客户端路由导航

**评估**：创造性最强，审查员不易找到相同的现有技术。建议优先撰写。

---

### 🏆 Case 2：P-01 — 基于分层多 Agent 路由的多产品线智能问答系统

**专利主题**：一种面向多产品线技术支持的分层 Agent 路由方法与系统

**独权方向**：
1. 第一 Agent 接收用户输入，输出结构化路由决策（语言/产品/范围/意图）
2. 根据路由决策选择绑定特定知识库的第二 Agent
3. 将用户原始查询替换为跨语言扩写后的优化查询注入对话历史
4. 第二 Agent 使用优化查询检索产品专属向量库并流式生成回答

**评估**：系统性强，覆盖面广。可包含 P-06、P-07 作为从属权利要求。

---

### 🏆 Case 3：P-04 — 精确搜索与语义搜索双通道异步融合方法

**专利主题**：一种基于客户端预分块与服务端向量检索的混合搜索方法

**独权方向**：
1. 构建时按标题切分文档为段落级内容块并缓存于客户端
2. 用户输入即时触发客户端精确匹配（三级优先级打分）
3. 输入稳定后异步触发服务端语义搜索
4. 基于 anchor 粒度去重合并两路结果
5. 语义结果追加替换精确结果中的重叠项

**评估**：创造性中等，但实用性强。"构建时预分块 + 运行时零延迟"的架构有独特价值。

---

### 🥈 Case 4：P-05 — 面向 AI 服务的智能告警分级处理方法

**专利主题**：一种基于规则分类引擎的 AI 服务异常告警分级方法

**独权方向**：
1. 将异常日志与预定义规则集进行正则匹配
2. 根据匹配结果分类为四个处理等级
3. 对突发类异常维护滑动窗口计数器，达阈值后触发告警
4. 对默认类异常进行指纹去重并周期性汇总发送

**评估**：建议聚焦"AI Agent 运行时监控"场景差异化叙述。

---

### 🥈 Case 5：P-06 合并 P-01 — 对话流中的智能推荐与留资方法（备选）

可作为 Case 2 的从属或独立小专利，聚焦"三阶段流水线（Triage 意图识别 → AI 回答 → 推荐 Widget 注入）"的交互方法。

---

## 五、下一步

请确认以上清单后，我将针对您选定的 Case 生成完整的**技术交底书大纲**，包括：
1. 发明名称
2. 技术领域
3. 背景技术（对标现有技术缺陷）
4. 发明内容（技术问题 + 技术方案 + 有益效果）
5. 具体实施方式（含流程图描述、代码映射）
6. 权利要求书草案（独立权利要求 + 从属权利要求）
