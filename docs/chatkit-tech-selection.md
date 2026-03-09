# ChatKit 集成方案技术选型报告

> 项目：FF Master 机器人用户手册 AI 问答系统
> 日期：2026-03-06

---

## 1. 需求背景

为 FF Master 用户手册 H5 站点集成 AI 问答功能，核心需求如下：

| 需求 | 说明 |
|------|------|
| AI 问答 | 用户可通过对话获取手册内容，基于 RAG（检索增强生成） |
| 引用来源跳转 | AI 回答中展示引用来源，**点击后跳转到对应手册页面**（SPA 页内导航） |
| Agent 配置热更新 | 修改 AI 的 prompt、模型、知识库等配置时，**无需修改和重新部署服务端代码** |
| 流式输出 | 回答以流式方式逐步呈现，保证交互体验 |

其中"引用来源点击跳转"是本次选型的**关键决策因素**。

## 2. ChatKit 渲染架构约束

OpenAI ChatKit 的 UI 在 **OpenAI 托管的 iframe** 中渲染（无论使用托管还是自托管后端），这意味着：

- 无法通过 DOM 事件捕获拦截 iframe 内部的点击
- 无法使用 MutationObserver 监听 iframe 内部的 DOM 变化
- 只能通过 ChatKit 官方提供的 API（options、events、methods）与 iframe 通信

ChatKit 提供三种 Annotation Source 类型，**点击行为各不相同**：

| Source 类型 | 渲染方式 | 点击行为 | 可被前端拦截 |
|---|---|---|---|
| `FileSource` | 文件引用标签 | iframe 内部处理（打开/下载文件） | **否** |
| `URLSource` | URL 链接标签 | iframe 内部处理（打开外部链接） | **否** |
| `EntitySource` | 可交互实体标签 | 触发前端 `entities.onClick` 回调 | **是** |

只有 `EntitySource`（且设置 `interactive: true`）才会触发前端可拦截的 `entities.onClick` 回调。

## 3. 三种候选方案

### 方案 A：AgentBuilder 托管后端（推荐集成）

OpenAI 官方推荐的最简集成方式。后端完全由 OpenAI 托管和运维。

**架构：**

```
前端 ChatKit ──(client_secret)──→ OpenAI 托管服务器（AgentBuilder Workflow）
```

**数据流：** 前端通过 `client_secret` 直接与 OpenAI 服务器通信，开发者的服务器仅负责创建 session，不参与对话数据传输。

**引用处理：** AgentBuilder 内部使用 `ResponseStreamConverter` 默认实现，将 `file_citation` 转换为 `FileSource`：

```python
# AgentBuilder 默认行为
async def file_citation_to_annotation(self, file_citation):
    return Annotation(
        source=FileSource(filename=filename, title=filename),  # FileSource → 不触发 onClick
        index=file_citation.index,
    )
```

| 维度 | 评价 |
|------|------|
| 接入成本 | ⭐⭐⭐ 极低，几乎零后端代码 |
| 运维负担 | ⭐⭐⭐ 无，OpenAI 全托管 |
| Agent 配置更新 | ⭐⭐⭐ 在 AgentBuilder UI 中修改即时生效 |
| **引用点击跳转** | **❌ 不支持**。引用使用 `FileSource`，点击在 iframe 内部处理，无法拦截 |
| 数据控制 | ⭐ 对话数据存储在 OpenAI |
| 自定义程度 | ⭐ 无法自定义引用渲染方式、无法注入自定义逻辑 |

**结论：因不满足"引用点击跳转"核心需求，排除。**

---

### 方案 B：Agents SDK 导出 + 自托管 ChatKit Server

在 AgentBuilder 中可视化设计 Agent workflow，导出为 Agents SDK 代码，在自托管服务器中运行。通过自定义 `ResponseStreamConverter` 将 `FileSource` 替换为 `EntitySource`。

**架构：**

```
AgentBuilder ── 导出 SDK 代码 ──→ 自托管 ChatKit Server（Agents SDK）
                                        │
                                  ChatKit 前端 (entities.onClick ✓)
```

**引用处理：** 通过继承 `ResponseStreamConverter`，覆盖 `file_citation_to_annotation` 方法：

```python
class CustomConverter(ResponseStreamConverter):
    async def file_citation_to_annotation(self, file_citation):
        page_info = FILE_SLUG_MAP.get(file_citation.filename)
        return Annotation(
            source=EntitySource(id=slug, title=title, interactive=True, data={"slug": slug}),
            index=file_citation.index,
        )

# 在 respond 方法中使用
async for event in stream_agent_response(context, result, converter=CustomConverter()):
    yield event
```

| 维度 | 评价 |
|------|------|
| 接入成本 | ⭐⭐ 中等，需自建服务器 |
| 运维负担 | ⭐⭐ 需自行维护服务器 |
| Agent 配置更新 | **❌ 差。每次在 AgentBuilder 修改后需重新导出代码并部署** |
| **引用点击跳转** | ✅ 支持。通过自定义 Converter 输出 `EntitySource` |
| 数据控制 | ⭐⭐⭐ 完全自主 |
| 自定义程度 | ⭐⭐⭐ 高，可自定义所有行为 |

**结论：支持引用点击，但 Agent 配置与代码耦合，每次调整 prompt/工具/模型都需要重新部署，维护成本高。排除。**

---

### 方案 C：Assistants API + 自托管 ChatKit Server（当前方案 ✅）

使用 OpenAI Assistants API 作为 AI 推理层，Agent 配置（prompt、model、file_search 知识库）托管在 OpenAI 侧。自建 ChatKit Server 作为桥接层，负责协议转换和引用来源映射。

**架构：**

```
┌─────────────────────┐      ┌─────────────────────────────┐      ┌──────────────┐
│  OpenAI Platform    │      │  自托管 ChatKit Server       │      │ ChatKit 前端  │
│                     │      │  (FastAPI)                   │      │              │
│  Assistant 配置      │ ←──→ │  Assistants API 调用         │ ←──→ │ entities     │
│  (prompt/model/     │      │  + file_citation → Entity-   │      │  .onClick    │
│   file_search)      │      │    Source 映射               │      │  (SPA 导航)   │
│                     │      │                              │      │              │
│  Vector Store       │      │  sidebar-*.json 映射表       │      │  React       │
│  (文档知识库)        │      │  (filename → page slug)     │      │  Router      │
└─────────────────────┘      └─────────────────────────────┘      └──────────────┘
      配置层（免部署）               运行层（桥接 + 映射）              展示层
```

**引用处理：** 服务端收集 Assistants API 返回的 `file_citation`，通过 `sidebar.json` 映射为页面 slug，输出 `EntitySource`：

```python
# file_citation.file_id → filename → sidebar slug → EntitySource
Annotation(
    source=EntitySource(
        id=slug,                     # 页面路由
        title=page_info["title"],    # 页面标题
        interactive=True,            # 允许点击
        data={"slug": slug},         # 传递给前端 onClick 的数据
    ),
    index=end_index,
)
```

前端通过 `entities.onClick` 拦截点击，执行 SPA 导航：

```typescript
entities: {
  onClick: (entity) => {
    const slug = entity.data?.slug
    navigate(url.pathname)           // React Router SPA 导航
    document.getElementById(hash)    // 滚动到锚点
      ?.scrollIntoView({ behavior: 'smooth' })
  },
},
```

| 维度 | 评价 |
|------|------|
| 接入成本 | ⭐⭐ 中等，需自建服务器 |
| 运维负担 | ⭐⭐ 需自行维护服务器 |
| Agent 配置更新 | **✅ 好。在 OpenAI Dashboard 修改 Assistant 即时生效，无需改代码** |
| **引用点击跳转** | **✅ 支持。`EntitySource` + `entities.onClick` 实现 SPA 页内导航** |
| 数据控制 | ⭐⭐ 对话数据经自有服务器，可审计/过滤 |
| 自定义程度 | ⭐⭐⭐ 高，完全控制引用映射和流式事件 |

**结论：同时满足"引用点击跳转"和"配置免部署更新"两个核心需求。采用。**

## 4. 方案对比总结

| | 方案 A：AgentBuilder 托管 | 方案 B：Agents SDK 导出 | **方案 C：Assistants API（当前）** |
|---|:---:|:---:|:---:|
| 引用点击跳转（SPA 导航） | ❌ | ✅ | **✅** |
| Agent 配置免部署更新 | ✅ | ❌ | **✅** |
| 自建服务器 | 不需要 | 需要 | **需要** |
| 引用类型 | `FileSource`（不可拦截） | `EntitySource`（可拦截） | **`EntitySource`（可拦截）** |
| 配置管理位置 | AgentBuilder UI | 代码中 | **OpenAI Dashboard** |
| 后端代码量 | ~0 | 中等 | **中等** |
| RAG 实现 | AgentBuilder 内置 | Agents SDK file_search | **Assistants API file_search** |

## 5. 选型决策

**最终选择方案 C（Assistants API + 自托管 ChatKit Server）**，核心原因：

1. **引用点击跳转是刚需。** 用户手册场景下，AI 回答中的引用来源必须能跳转到对应手册页面。ChatKit iframe 架构下，只有 `EntitySource` 能触发 `entities.onClick`，方案 A 不可行。

2. **配置与代码分离。** Assistant 的 prompt、model、知识库等配置托管在 OpenAI 侧，通过 Dashboard 修改即时生效。服务端仅包含协议桥接逻辑（稳定不变）和文件名→页面的映射逻辑（跟随文档结构变化），无需因 Agent 调优而频繁部署。方案 B 不满足此要求。

3. **RAG 零运维。** 文档检索完全由 OpenAI 托管的 `file_search` + Vector Store 处理，无需自建向量数据库或维护 embedding pipeline。

4. **可控的复杂度。** 自建 ChatKit Server 的代码量可控（约 400 行 Python），核心逻辑清晰：Assistants API 流式调用 → 引用映射 → ChatKit 协议事件输出。

## 6. 已知局限与后续演进

| 项目 | 现状 | 后续可考虑 |
|------|------|-----------|
| 会话存储 | 内存存储（InMemoryStore），重启丢失 | 接入 PostgreSQL / Redis 持久化 |
| 引用粒度 | 文件级（跳转到整个页面） | 段落级（跳转到页面内具体章节） |
| 并发能力 | 单实例 FastAPI | 多实例 + 负载均衡 |
| 监控 | 基础日志 | 接入 APM（延迟、token 用量、错误率） |
| ChatKit 版本跟进 | — | 如未来 AgentBuilder 支持自定义 `EntitySource`，可评估回迁到方案 A |
| 模型选择 | 需确保模型对 Assistants API file_search 的 `file_citation` 标注兼容 | 关注 OpenAI 新模型兼容性，择机升级 |
