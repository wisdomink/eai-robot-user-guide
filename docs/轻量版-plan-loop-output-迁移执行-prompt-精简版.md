# 轻量版 Plan -> Loop -> Output 迁移执行 Prompt（精简版）

请直接在当前仓库中完成实现，把聊天后端从现有的 `triage -> support -> recommendation`，升级为**轻量版** `plan -> loop -> output -> recommendation`。不要只给方案，请直接改代码。

## 背景

当前核心后端在：

- `apps/rag-api/app/services/chatkit_handler.py`

当前问题是：当用户同时问“产品 + 价格 + 最近新闻”时，系统会把 `产品库 + 价格库 + 新闻库` 三个 vector stores 一起传给 `FileSearchTool`，但 OpenAI 当前只允许最多 2 个，因此会报错：

- `Invalid input: maximum of 2 vector stores allowed.`

仓库里已经有一个临时止血补丁： `_build_support_vector_store_ids()` 会把库数量截断到 2 个。现在要做的是**正式方案**，通过多轮检索解决，而不是简单截断。

## 目标

请实现以下结构：

1. `PlanAgent`
   - 保留当前 triage 的核心能力：识别 `input_lang`、`query_scope`、`query_type`
   - 额外输出可执行的 plan，例如：
     - 是否需要价格
     - 是否需要新闻
     - 后续需要执行几轮 retrieval
     - 每轮 retrieval 的目标是什么

2. `Loop Orchestrator`
   - 必须由服务端代码控制，不要完全交给 agent 自由决定
   - 按 plan 执行 1~N 轮 retrieval
   - 每轮 `vector_store_ids` 必须最多 2 个
   - 对于“产品 + 价格 + 新闻”场景，至少拆成两轮：
     - pass 1: `产品库 + 价格库`
     - pass 2: `产品库 + 新闻库`

3. `OutputAgent`
   - 不直接做多库检索
   - 接收原问题、plan、各轮 retrieval 结果
   - 负责汇总、去重、冲突消解，并生成最终回答

4. `Recommendation`
   - 保持当前 recommendation / lead capture / widget 流程不变

## 约束

- 这是轻量版演进，不是推翻重写
- 优先复用当前 `chatkit_handler.py` 的结构
- 保留现有 ChatKit streaming 体验
- loop 的执行过程要有清晰日志
- 不要破坏现有 recommendation 流程
- 不要仅保留“最多 2 个库”的截断作为最终方案
- 不要回滚仓库中与你这次任务无关的已有改动

## 建议实现

- 以 `chatkit_handler.py` 为主进行改造
- 可以把 `TriageOutput` 升级为 `PlanOutput`，或保留兼容层但新增 plan 字段
- 新增 helper 来：
  - 按显式 `vector_store_ids` 构建 retrieval agent
  - 执行单轮 retrieval pass
  - 执行最终 output 汇总
- 普通问题尽量仍然只走单轮，避免不必要复杂度
- 复合问题走多轮 retrieval + 最终汇总

## 验收标准

- 单一问题仍能正常回答
- “产品 + 价格 + 新闻”场景不再触发 3 个 vector stores 同时检索
- 能通过多轮 retrieval + output agent 汇总完成最终回答
- recommendation 逻辑未被破坏
- 修改后的代码结构比当前更清晰

## 执行要求

请完成以下工作：

1. 阅读并理解当前 `chatkit_handler.py`
2. 直接实现轻量版 `plan -> loop -> output`
3. 保留并补充日志，至少能看出：
   - plan 结果
   - loop 执行了几轮
   - 每轮用了哪些 `vector_store_ids`
   - output agent 是否成功
4. 做基本验证
   - 检查修改文件的语法/lint
   - 至少确认不会再出现 3 个 vector stores 直接传入 `FileSearchTool`
5. 最终输出：
   - 改了什么
   - 为什么这样设计
   - 如何验证
   - 剩余风险

