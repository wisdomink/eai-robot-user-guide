# Agent Prompt 重构清单

下面这段文字可以直接复制到一个新 chat 中，作为继续重构当前 FF Robot 多 agent 架构的任务提示词。

```md
请基于当前仓库的真实运行逻辑，而不是历史文档描述，梳理并重构 `apps/rag-api/app/services/` 下的多 agent prompt 架构。

目标：
1. 以当前实际生效的 `plan -> loop -> output -> recommendation` 工作流为准。
2. 明确各个 agent 的职责边界：Router Agent、Product Retrieval Agents、Price Agent、News Agent、Fallback Agent、Output Agent。
3. 不再把 `query_scope` 作为高优先级路由主开关；是否进入兜底，应由“是否命中任何可执行领域”决定。
4. `output.md` 是唯一对用户输出最终答案的 agent prompt，其它 prompt 都只能输出中间检索结果或路由结果。
5. 所有正在生效的 prompt 资产应尽量收敛到 `apps/rag-api/app/services/instructions/*.md`，避免核心 prompt 长期散落在代码里。

请先完成下面的梳理，再实施修改：

## 第一部分：现状梳理
1. 读取 `apps/rag-api/app/services/chatkit_handler.py`
2. 读取 `apps/rag-api/app/services/instructions/plan.md`
3. 读取 `apps/rag-api/app/services/instructions/output.md`
4. 读取所有当前生效的产品检索 prompt
5. 明确哪些 prompt 仍写死在代码里，哪些已经文件化
6. 输出一份简短结论：
   - 当前真实 agent 链路
   - 每个 agent 的输入 / 输出 / 是否对客
   - 已过时或职责混乱的 prompt

## 第二部分：重构目标
请按下面的目标进行重构：

### Router Agent
- 仅负责：语言识别、产品识别、领域路由、查询扩写、购买意图、推荐命中
- 不负责：最终拒答文案、最终客服表达、把 `out-of-scope` 当产品类型输出
- 输出字段建议保留：
  - `input_lang`
  - `query_type`
  - `product_types`
  - `needs_product`
  - `needs_price`
  - `needs_news`
  - `purchase_intent`
  - `query_text`
  - `recommendation_hit`
  - `recommendation_rule_id`

### Retrieval Agents
- Product / Price / News 全部只输出结构化检索摘要
- 不输出最终客服口吻
- 不做留资引导
- 不做内部机制说明

### Fallback Agent
- 只在没有命中任何产品 / 价格 / 新闻领域时触发
- 输出供 Output Agent 使用的兜底中间结果

### Output Agent
- 唯一对客
- 负责汇总、去重、冲突消解、推理和表达
- 对价格类和比较类问题优先直接给结论

## 第三部分：代码与 Prompt 改造要求
1. 调整路由 schema，使其与新的 Router Agent 输出一致
2. 调整 loop pass 生成逻辑：
   - 先按 `needs_product / needs_price / needs_news` 生成 passes
   - 如果没有任何 pass，再进入 fallback
3. 将价格和新闻 prompt 文件化到 `instructions/`
4. 更新 `plan.md`、`fallback.md`、`output.md`
5. 如有必要，更新 `README.md` 说明当前真实架构

## 第四部分：交付要求
1. 直接修改代码和 prompt 文件
2. 给出最终变更摘要
3. 说明哪些历史概念已经废弃
4. 说明是否做了基础校验
```

## 推荐使用方式

如果希望新 chat 直接开始执行，可以在上面提示词前再补一句：

```md
请直接完成重构，不只分析；改完后给我一个简短变更总结。
```
