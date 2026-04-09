# AI 助手推荐能力升级方案

## 1. 方案背景

当前官网 AI 助手已经具备以下能力：

- 支持多产品问答路由
- 支持基于产品手册的 RAG 检索与回答
- 支持回答后插入推荐卡片
- 支持推荐配置管理页与推荐配置接口

当前推荐能力的主要问题是：

- 推荐逻辑较静态，无法根据运营配置灵活切换推荐产品
- 推荐文案与推荐规则耦合在代码中，运营调整成本较高
- 路由 Agent 还没有结合运营配置进行推荐意图判断
- 推荐内容虽然可以展示，但缺少一套清晰、可汇报、可落地的升级方案

本次方案的目标，是在不推翻现有 ChatKit + Triage + Support Agent 架构的前提下，完成一轮低风险、可运营、可持续迭代的推荐能力升级。

## 2. 本次升级目标

- 让推荐产品从固定推荐升级为运营可配置推荐
- 让路由 Agent 可以基于运营配置动态判断是否触发推荐
- 让推荐文案由运营维护，减少模型自由生成带来的不可控风险
- 让推荐继续以回答后追加图鉴卡片的形式出现，保持低打扰
- 在现有代码结构上平滑升级，避免大规模重构

## 3. 本次方案结论

本次会议建议确认以下 3 个最终决策：

1. `recommendations.json` 使用中英文双文案字段
2. triage Agent 改为动态构建 prompt，推荐规则信息来自 `/api/get-recommendations`
3. 推荐内容以“回答后追加图鉴卡片”的形式展示，不混入主回答正文

## 4. 推荐配置方案

### 4.1 配置来源

推荐规则由运营通过推荐管理页维护，后端通过 `/api/get-recommendations` 提供统一读取能力。

当前推荐管理链路已经具备：

- 推荐管理页面：`src/pages/RecommendationRecordsPage.tsx`
- 推荐接口：`/api/get-recommendations`
- 推荐保存接口：`/api/save-recommendation`
- 推荐删除接口：`/api/delete-recommendation/{id}`
- 推荐配置持久化：`recommendations.json`

### 4.2 推荐配置字段

本次方案采用以下字段作为标准配置结构：

- `id`：推荐规则唯一标识
- `enabled`：是否启用
- `product_name`：推荐产品名称
- `trigger_scene`：触发推荐场景
- `recommendation_content_cn`：中文推荐文案
- `recommendation_content_en`：英文推荐文案

### 4.3 设计原则

- 推荐产品由运营决定，不在代码中写死
- 推荐文案由运营维护，不由模型自由生成
- 推荐规则支持中英文双语，以适配当前 AI 助手多语言问答能力

## 5. Triage Agent 升级方案

### 5.1 当前问题

当前 triage Agent 是静态初始化的，提示词内容固定，不适合承载动态推荐规则。

因此，本次需要将 triage Agent 的构建方式从“模块初始化时静态创建”升级为“每次请求时动态构建”。

### 5.2 升级方向

新增专门的 triage prompt 构建方法，在每次请求时执行：

1. 读取当前启用的推荐规则
2. 将推荐规则整理为适合模型判断的 prompt 片段
3. 动态构建本次请求的 triage Agent
4. 让 triage Agent 在保留现有路由职责的基础上，额外输出推荐命中结果

### 5.3 推荐规则注入方式

推荐规则不建议由 triage Agent 自己去请求接口，而应由后端代码先读取配置，再拼接进 prompt。

推荐实现建议：

- 对外数据来源：`/api/get-recommendations`
- 对内代码实现：直接复用推荐存储层或推荐服务层，读取相同数据源

这样做的好处是：

- 避免服务内部再发 HTTP 请求给自己
- 减少额外网络开销和失败点
- 保证推荐管理页和 triage 读取同源数据

### 5.4 Triage 输出建议

在保留现有字段的基础上，新增两个推荐相关字段：

- `recommendation_hit`
- `recommendation_rule_id`

建议输出结构如下：

```json
{
  "input_lang": "cn",
  "query_scope": "robot-website",
  "query_type": "aegis-edu",
  "purchase_intent": "no",
  "query_text": "How to use ...",
  "recommendation_hit": "yes",
  "recommendation_rule_id": "inspection_aegis_ultra"
}
```

### 5.5 设计原则

- triage Agent 只负责判断是否命中推荐规则
- triage Agent 不负责生成最终推荐文案
- triage Agent 不直接决定展示样式
- triage Agent 不应污染主回答所使用的检索逻辑

## 6. 推荐文案生成方案

### 6.1 最终结论

最终推荐文案由运营配置提供，不由模型生成。

### 6.2 采用该方案的原因

- 文案可控，避免模型生成不稳定或过度营销的内容
- 运营可随时调整推荐话术，无需改代码或改 prompt
- 中英文文案可分别配置，减少翻译误差
- 推荐展示内容与后台配置一一对应，便于埋点、复盘和排查

### 6.3 角色分工

- 运营：维护推荐产品、触发场景、推荐文案
- triage Agent：判断是否命中某条推荐规则
- recommendation engine：根据命中结果读取对应推荐文案
- ChatKit 响应链路：在回答后追加推荐卡片

## 7. 关于 `query_text` 的处理原则

会议中已讨论“命中推荐时是否直接扩写 `query_text`”。

本次方案建议明确为：

- 不将推荐产品信息直接写入主 `query_text`
- 主 `query_text` 仍然只服务于当前用户问题的 RAG 检索
- 推荐链路通过独立字段 `recommendation_rule_id` 传递

### 7.1 原因

- 避免主问题检索被推荐产品干扰
- 避免用户明明在问 A 产品，却检索到 B 产品资料
- 避免推荐逻辑污染主回答质量

### 7.2 最终原则

- 主回答链路解决“当前问题”
- 推荐链路解决“下一步建议”
- 两条链路并行工作，不互相混淆

## 8. 推荐展示方案

### 8.1 展示形式

本次方案确定继续采用“回答后追加图鉴卡片”的形式。

### 8.2 采用该形式的原因

- 与当前 ChatKit widget 能力兼容
- 对用户打扰较低
- 不会破坏主回答结构
- 后续可扩展为更丰富的图鉴样式或 CTA 按钮

### 8.3 第一版图鉴卡片建议

第一版卡片可以包含以下内容：

- 标题：推荐产品名
- 正文：推荐文案
- 可选标签：`推荐产品` / `Recommended Product`

第一版先不强制增加复杂交互，重点验证推荐命中与展示链路是否稳定。

## 9. 整体流程设计

本次升级后的推荐流程如下：

1. 运营在推荐管理页维护推荐规则
2. 推荐规则保存到 `recommendations.json`
3. 用户发起对话请求
4. 后端读取当前启用的推荐规则
5. 后端动态构建 triage prompt
6. triage Agent 输出基础路由结果和推荐命中结果
7. support Agent 按原有流程完成主回答
8. 回答完成后，系统根据 `recommendation_rule_id` 读取对应推荐文案
9. 通过图鉴卡片追加展示推荐内容

## 10. 实施范围

本次改动主要涉及以下模块：

- `apps/rag-api/app/services/instructions/plan.md`
- `apps/rag-api/app/services/chatkit_handler.py`
- `apps/rag-api/app/services/recommendation_engine.py`
- `apps/rag-api/app/main.py`
- `apps/rag-api/app/services/recommendation_catalog_service.py`
- `src/pages/RecommendationRecordsPage.tsx`
- `src/api/recommendations.ts`
- `apps/rag-api/app/services/recommendations.json`

## 11. 预期收益

- 推荐能力从固定逻辑升级为运营可配置逻辑
- 推荐产品与推荐文案支持动态调整
- triage Agent 能更智能地识别推荐场景
- 推荐内容以低打扰方式承接主回答，提升整体体验
- 后续可继续扩展推荐排序、CTA 跳转、推荐点击埋点和实验机制

## 12. 风险与注意事项

### 12.1 Prompt 风险

如果将推荐规则原文无约束地注入 triage prompt，可能导致模型输出不稳定。

建议：

- 只注入启用中的规则
- 仅传入 triage 所需的精简字段
- 要求 triage 只能从给定规则中选择 `recommendation_rule_id`

### 12.2 推荐误判风险

如果推荐场景描述过于宽泛，可能导致误触发。

建议：

- 运营侧对 `trigger_scene` 使用更明确的业务描述
- 第一版优先配置少量高确定性规则

### 12.3 回答质量风险

如果将推荐产品直接写入主检索查询，可能污染主回答结果。

建议：

- 推荐逻辑与主回答检索逻辑分离
- 不把推荐产品名直接写入主 `query_text`

## 13. 本次会议建议确认项

建议会议最终确认以下事项：

1. 推荐配置以中英文双文案字段为标准结构
2. triage Agent 改为动态构建，并读取推荐规则
3. triage 输出新增 `recommendation_hit` 和 `recommendation_rule_id`
4. 推荐文案由运营配置提供，不由模型生成
5. 推荐展示使用回答后追加图鉴卡片的形式
6. 不将推荐产品信息直接混入主 `query_text`

## 14. 下一步实施建议

建议开发按以下顺序推进：

1. 先调整 triage 输出结构与 triage prompt 构建方式
2. 再改造 recommendation engine 的匹配逻辑
3. 最后接入回答后图鉴卡片展示

这样可以保证改造路径清晰，联调成本最低，也更适合分阶段验收。
