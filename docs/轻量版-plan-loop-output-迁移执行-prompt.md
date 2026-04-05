# 轻量版 Plan -> Loop -> Output 迁移执行 Prompt

请在当前项目中，将现有聊天后端从 `triage -> support -> recommendation` 的主流程，升级为**轻量版** `plan -> loop -> output -> recommendation` 架构。请直接完成代码实现，不要只给方案。

## 项目背景

当前项目是一个基于 ChatKit + OpenAI Agents SDK 的机器人官网聊天系统，核心后端逻辑在：

- `apps/rag-api/app/services/chatkit_handler.py`

当前主流程大致为：

1. `triage agent` 识别语言、产品、query scope、价格/新闻等意图
2. `support agent` 直接携带 `FileSearchTool(vector_store_ids=...)` 检索并流式回答
3. `recommendation engine` 在回答后决定是否展示推荐卡片或留资表单

最近线上已经暴露出一个架构问题：当用户同时询问“产品 + 价格 + 最近新闻”时，后端会尝试把 `产品知识库 + 价格知识库 + 新闻知识库` 同时塞给 `FileSearchTool`，而 OpenAI 当前限制 **最多 2 个 vector stores**，导致报错：

- `Invalid input: maximum of 2 vector stores allowed.`

目前仓库中已经有一个**临时止血补丁**：在 `_build_support_vector_store_ids()` 中把 vector store 数量限制到最多 2 个，优先顺序为：

- `产品库 -> 价格库 -> 新闻库`

这个补丁只能避免报错，但不能真正解决“复合问题需要多轮检索”的问题。现在要做的是：在不推翻现有项目的前提下，把主流程演进为轻量版 `plan -> loop -> output`。

## 目标

请把当前实现改造成如下结构：

1. `PlanAgent`
   - 负责理解用户问题
   - 保留现有 triage 的能力：识别 `input_lang`、`query_scope`、`query_type`
   - 在此基础上，产出一个更适合后续执行的结构化 plan
   - 这个 plan 至少要能表达：
     - 当前产品类型
     - 是否需要价格信息
     - 是否需要新闻/动态信息
     - 后续需要执行的 retrieval passes
     - 最终输出语言

2. `Loop Orchestrator`
   - 使用**服务端代码**而不是完全交给 agent 自主决定
   - 根据 plan 逐步执行 1~N 次 retrieval pass
   - 每一轮 retrieval pass 的 `vector_store_ids` 必须满足 OpenAI 的限制：**最多 2 个**
   - 典型场景：
     - 普通问题：1 次检索
     - 同时问价格和新闻：拆成 2 次检索
       - pass 1: `产品库 + 价格库`
       - pass 2: `产品库 + 新闻库`

3. `OutputAgent`
   - 不再直接做多库检索
   - 接收：
     - 用户原问题
     - Plan 输出
     - Loop 中每一轮 retrieval 的中间结果
   - 负责：
     - 汇总答案
     - 去重
     - 信息冲突时优先更直接、更明确、更新近的内容
     - 输出最终自然语言回答

4. `Recommendation`
   - 继续保留当前回答后的 recommendation / lead-capture 逻辑
   - 不要因为这次改造破坏现有 recommendation 流程

## 约束

请严格遵守以下约束：

1. 这是**轻量版演进**，不是推翻重写
   - 尽量复用现有 `chatkit_handler.py` 中的结构
   - 不要引入与当前项目不匹配的重量级框架

2. Loop 的执行控制权必须在服务端代码中
   - 不要把“先查哪个库、再查哪个库、查几轮”完全交给模型自由决定
   - 要保证每一轮检索可控、可记录、可调试

3. 必须保留现有 streaming 体验
   - 最终对前端的回答仍应通过当前 ChatKit 流式输出机制返回
   - 如果中间 retrieval pass 不适合直接流式给用户，可以在服务端内部先执行并收集结果

4. 要尽量保持现有日志和 trace 的可读性
   - 新架构下应能看到：
     - plan 结果
     - 每轮 loop 执行了什么
     - 每轮使用了哪些 `vector_store_ids`
     - 最终 output agent 是否成功汇总

5. 不要破坏现有 recommendation/lead-capture/card widget 流程

6. 不要仅仅保留当前“最多 2 个库”的截断策略作为最终方案
   - 最终实现应让“价格 + 新闻”场景通过多轮检索完成，而不是简单丢弃新闻或价格

## 实现建议

请优先采用以下实现思路：

### 一、Plan 层

- 可以把当前 `TriageOutput` 升级为新的结构化输出，例如 `PlanOutput`
- 也可以保留兼容层，但最终需要让 plan 具备“执行计划”能力
- 推荐在 plan 中显式表达 `retrieval_tasks` 或 `retrieval_passes`

例如，一个“介绍一下 aegis，它的价格和最近的新闻？”这类请求，plan 应能表达出类似意图：

- `query_type = aegis`
- `needs_price = yes`
- `needs_news = yes`
- `retrieval_passes = [product+price, product+news]`

### 二、Loop 层

- 新增服务端 helper，按显式给定的 `vector_store_ids` 构建 support/retrieval agent
- 每轮 retrieval pass 可以复用产品 support instructions，但要增加本轮 focus 约束
- 每轮 pass 最好返回结构化或至少稳定的文本结果，供后续 output agent 汇总
- 普通单一问题时，应尽量避免引入额外复杂度，仍然走一轮即可

### 三、Output 层

- 新增一个不带 file_search tools 的输出/汇总 agent
- 输入为：
  - 原始用户问题
  - plan
  - loop 各轮结果
- 输出为用户最终看到的回答

## 建议修改范围

优先集中在以下位置：

- `apps/rag-api/app/services/chatkit_handler.py`

如有必要，可以补充修改：

- `apps/rag-api/app/services/instructions/*.md`
- 与 plan/output agent 对应的新增 prompt / instruction 模板

请尽量避免无关大范围改动。

## 你需要完成的工作

请按下面顺序执行：

1. 先阅读当前 `chatkit_handler.py`，梳理：
   - triage 的输入输出
   - support agent 的构建方式
   - 当前流式输出和 recommendation 的挂接点

2. 设计并实现轻量版 `plan -> loop -> output`
   - 尽量少改动无关代码
   - 但不要为了“少改”而牺牲结构清晰度

3. 替换当前“复合问题直接单轮 support”的实现
   - 尤其要覆盖 `needs_price=yes && needs_news=yes` 的场景

4. 保留并补充日志
   - 能让人一眼看出本次请求：
     - plan 是什么
     - loop 执行了几轮
     - 每轮查了哪些库
     - output 是否成功

5. 做基本验证
   - 至少确认不会再出现 3 个 vector stores 直接传入 `FileSearchTool` 的问题
   - 检查被修改文件的 lints / 语法问题
   - 如有合适的测试位置，可增加小而有价值的测试；没有也可以只做运行级校验，但要说明

## 验收标准

最终实现至少应满足：

1. 单一问题场景仍可正常回答
2. “产品 + 价格 + 新闻”场景不再依赖 3 个 vector stores 同时检索
3. 系统能够通过多轮 retrieval + 最终 output 汇总完成回答
4. recommendation 逻辑未被破坏
5. 代码结构比现在更清晰，而不是只在现有逻辑上继续堆 if/else
6. 修改完成后，给出简明说明：
   - 改了什么
   - 为什么这样设计
   - 如何验证
   - 当前剩余风险是什么

## 额外要求

- 只在必要时新增 helper / instruction 文件
- 保持 Python 代码风格和当前项目一致
- 不要动无关前端代码，除非后端协议变化确实要求联动
- 如果发现当前仓库中有与你这次改动无关的脏改动，不要覆盖或回滚它们

## 交付方式

请直接在仓库中完成修改，并在结束时输出：

1. 本次迁移的核心改动说明
2. 涉及的关键文件
3. 验证结果
4. 如未完成某些验证，明确说明原因

