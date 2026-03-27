# AI 助手推荐能力升级方案

## 目标

- 推荐产品从固定逻辑升级为运营可配置
- AI 问答过程中能识别是否需要触发推荐
- 用低打扰方式展示推荐

## 推荐配置

推荐规则由运营通过后台维护，后端统一读取 `recommendations.json`。

配置字段：

| 字段 | 说明 |
|------|------|
| `enabled` | 是否启用 |
| `product_name` | 推荐产品名称 |
| `trigger_scene` | 触发场景 |
| `recommendation_content_cn` | 中文推荐文案 |
| `recommendation_content_en` | 英文推荐文案 |

## Triage Agent 改造

1. 每次请求前读取当前启用的推荐规则
2. 动态拼接推荐规则到 triage prompt
3. triage 输出新增 `recommendation_hit` 和 `recommendation_rule_id` 字段
4. triage 只判断是否命中，不生成推荐文案

## 展示方式

回答完成后追加推荐图鉴卡片，卡片包含：

- 推荐产品标题
- 推荐文案
- 推荐标签

## 整体流程

1. 运营维护推荐规则 → 保存到 `recommendations.json`
2. 用户发起问答 → 后端读取启用中的推荐规则
3. 动态构建 triage prompt → triage 输出是否命中推荐
4. support Agent 完成主回答 → 追加推荐图鉴卡片
