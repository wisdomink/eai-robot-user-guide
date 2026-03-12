# FF Robot RAG Server

FF Robot 全系列产品的 AI 后端服务，提供多 Agent 智能问答和语义搜索能力。

支持两种运行模式：
- **Backend 模式** — 自托管多 Agent 工作流（Triage + 5 个产品 Support Agent）
- **Agent Builder 模式** — 前端直连 OpenAI Agent Builder，后端仅创建 ChatKit session

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 异步 ASGI，支持 SSE 流式响应 |
| 对话协议 | [OpenAI ChatKit](https://github.com/openai/chatkit-python) | 线程管理、消息持久化、流式传输 |
| AI 推理 | OpenAI Agents SDK + FileSearchTool | 多 Agent 工作流，托管式文档检索 |
| LLM | gpt-5（可通过 `.env` 切换） | 对话生成，支持 reasoning |
| 语义搜索 | OpenAI Vector Store Search API | 跨页面中英文语义搜索 |

## 架构概览

### Backend 模式（默认）

```
用户提问 → ChatKit 协议 → POST /chatkit
                              │
                    ┌─────────▼──────────┐
                    │   Triage Agent      │  非流式，JSON 输出
                    │   语言检测 + 翻译    │  → input_lang
                    │   产品识别          │  → query_type
                    │   查询扩写          │  → query_text
                    └─────────┬──────────┘
                              │ 路由
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                  ▼
    Master Ultra      Futurist Ultra     ... General
    Support Agent     Support Agent      Support Agent
    (FileSearch)      (FileSearch)       (FileSearch)
            │                 │                  │
            └─────────────────┼──────────────────┘
                              ▼
                    FFRobotConverter
                    file_citation → EntitySource(slug)
                              │
                    _EventStreamRewriter
                    /images/... → 绝对 URL
                              │
                    SSE 流式返回 → 前端 ChatPanel
```

### Agent Builder 模式

```
前端 ChatPanel
  │ ① POST /api/chatkit/session
  ▼
后端 → openai.chatkit.sessions.create(workflow_id) → OpenAI
  │ ② 返回 client_secret
  ▼
前端 ←→ OpenAI Agent Builder（聊天直连，不经后端）
```

## 项目结构

```
rag_server/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI 入口
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                # 环境变量 + 路径常量
│   └── services/
│       ├── __init__.py
│       ├── chatkit_handler.py       # 多 Agent 工作流 + ChatKit 桥接
│       └── instructions/            # Agent Prompt 模板
│           ├── triage.md            # Triage Agent — 路由预处理
│           ├── master-ultra.md      # Master Ultra 技术支持
│           ├── futurist-ultra.md    # Futurist Ultra 技术支持
│           ├── aegis-ultra.md       # Aegis Ultra 技术支持
│           ├── aegis-edu.md         # Aegis EDU 技术支持
│           └── general.md           # 通用/跨产品支持
├── eval/
│   ├── run_eval.py                  # RAG 评测脚本
│   └── test_cases.json              # 测试用例
├── create_vector_store.py           # 创建 Vector Store 并上传文档
├── agent-builder-design.md          # Agent Builder 编排架构设计
├── agent_build_sdk_info             # Agent Builder 导出的 SDK 代码（参考）
├── .env                             # 环境变量（勿提交）
├── .env.example                     # 环境变量模板
├── requirements.txt                 # Python 依赖
├── server_run.sh                    # 一键启动脚本
└── README.md
```

## 快速开始

### 前置条件

- Python 3.10+
- OpenAI API Key
- OpenAI Vector Store（包含手册文档，每个产品一个 + 全量库一个）

### 1. 创建 Vector Store（首次部署）

```bash
cd rag_server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 编辑 .env，填入 OPENAI_API_KEY
python create_vector_store.py
```

脚本会读取 `src/content/sidebar.json`，将所有产品的 Markdown 文档上传到 OpenAI Vector Store。完成后将输出的 Vector Store ID 填入 `.env`。

### 2. 启动服务

**一键启动（推荐）：**

```bash
cd rag_server
chmod +x server_run.sh
./server_run.sh
```

脚本会自动完成：检查 Python → 校验 `.env` → 创建虚拟环境 → 安装依赖 → 启动服务。

默认端口 `8000`，可通过环境变量自定义：

```bash
RAG_PORT=9000 ./server_run.sh
```

**手动启动：**

```bash
cd rag_server
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## 环境变量

在 `.env` 文件中配置（参考 `.env.example`）：

### 基础配置

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API 密钥 |
| `LLM_MODEL` | | `gpt-5` | Agent 使用的 LLM 模型 |

### Chat 模式

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `CHAT_MODE` | | `backend` | `backend`（自托管）或 `agent-builder`（直连 OpenAI） |
| `AGENT_BUILDER_WORKFLOW_ID` | | `wf_69aa...` | Agent Builder 工作流 ID（仅 agent-builder 模式） |

### Vector Store（backend 模式必填）

| 变量 | 必填 | 说明 |
|------|:----:|------|
| `OPENAI_VECTOR_STORE_MASTER_ULTRA_ID` | ✅ | Master Ultra 产品文档库 |
| `OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID` | ✅ | Futurist Ultra 产品文档库 |
| `OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID` | ✅ | Aegis Ultra 产品文档库 |
| `OPENAI_VECTOR_STORE_AEGIS_EDU_ID` | ✅ | Aegis EDU 产品文档库 |
| `OPENAI_VECTOR_STORE_ROBOT_ALL_ID` | ✅ | 全量文档库（用于 General Agent + 语义搜索） |

### 其他

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `PUBLIC_BASE_URL` | | — | 应用公网地址，用于 ChatKit iframe 中图片 URL 重写 |

端口通过 shell 环境变量控制（不在 `.env` 中）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_PORT` | `8000` | 服务监听端口 |

## API 接口

| 端点 | 方法 | 模式 | 说明 |
|------|------|------|------|
| `/chatkit` | POST | backend | ChatKit 协议端点（线程管理 + 流式对话） |
| `/api/chatkit/session` | POST | agent-builder | 创建 ChatKit session，返回 `client_secret` |
| `/api/chat-mode` | GET | 通用 | 返回当前配置的 chat 模式 |
| `/search` | GET | 通用 | 语义搜索（`?q=查询词&limit=10`） |
| `/health` | GET | 通用 | 健康检查 |

## 多 Agent 工作流

### Triage Agent（路由预处理）

接收用户输入，输出结构化 JSON：

| 字段 | 说明 |
|------|------|
| `input_lang` | 用户语言：`cn`（中文）/ `en`（英文） |
| `query_type` | 产品路由：`master-ultra` / `futurist-ultra` / `aegis-ultra` / `aegis-edu` / `general` |
| `query_text` | 翻译为英文并扩写后的搜索查询，优化 RAG 检索质量 |

### Support Agent（产品技术支持）

每个产品有独立的 Support Agent，配置对应的 Vector Store 和 Prompt 模板：

| Agent | Vector Store | 文档范围 |
|-------|-------------|---------|
| Master Ultra Support | 独立库 | 21 篇 Master Ultra 手册 |
| Futurist Ultra Support | 独立库 | 16 篇 Futurist Ultra 手册 |
| Aegis Ultra Support | 独立库 | 14 篇 Aegis Ultra 手册 |
| Aegis EDU Support | 独立库 | 18 篇 Aegis EDU 手册 |
| General Support | 全量库 | 全部 69 篇手册文档 |

Agent 的 Prompt 模板位于 `app/services/instructions/`，支持 `{{input_lang}}` 和 `{{query_text}}` 变量插值。

## 引用来源跳转（Backend 模式）

AI 回答中的引用来源支持点击跳转到对应手册页面：

1. `FileSearchTool` 检索文档后，模型回答包含 `file_citation`
2. `FFRobotConverter` 通过 `sidebar.json` 将文件名映射为页面 slug
3. 输出 `EntitySource`（带 `data.slug`），前端 `entities.onClick` 拦截
4. 前端通过 React Router 执行 SPA 导航到对应页面

> Agent Builder 模式下引用会使用 OpenAI 默认样式，不支持 SPA 跳转。

## 切换 Chat 模式

### 切换为 Agent Builder 模式

1. 编辑 `rag_server/.env`：

```env
CHAT_MODE=agent-builder
```

2. 启动前端时设置环境变量：

```bash
VITE_CHAT_MODE=agent-builder ./client_run.sh
```

### 切换回 Backend 模式

1. 编辑 `rag_server/.env`：

```env
CHAT_MODE=backend
```

2. 正常启动前端：

```bash
./client_run.sh
```

### 两种模式对比

| 特性 | Backend 模式 | Agent Builder 模式 |
|------|-------------|-------------------|
| 聊天流量 | 全部经过自托管后端 | 前端直连 OpenAI |
| 后端职责 | 完整 Agent 工作流 + 流式处理 | 仅创建 session（1 次 API 调用） |
| 引用跳转 | ✅ SPA 页面内跳转 | ❌ 使用默认引用样式 |
| 图片 URL 重写 | ✅ 自动转为绝对路径 | ❌ 需要 Agent 生成绝对路径 |
| Agent 配置修改 | 修改代码后重启 | 在 Agent Builder 控制台修改 |
| 调试 | 本地日志 + OpenAI Traces | OpenAI Traces |

## 评测

内置评测工具用于验证 RAG 回答质量：

```bash
cd rag_server
python -m eval.run_eval                  # 运行全部测试用例
python -m eval.run_eval --ids 1 2 3      # 运行指定用例
python -m eval.run_eval --category safety # 按分类运行
```

## 注意事项

- 文档变更后需重新运行 `create_vector_store.py` 更新 Vector Store
- Agent 的 Instructions 模板在 `app/services/instructions/*.md` 中，修改后重启服务即生效
- `.env` 文件包含 API Key，已在 `.gitignore` 中排除，切勿手动提交
- `venv/` 目录为 Python 虚拟环境，已在 `.gitignore` 中排除
- Agent Builder 的工作流设计文档见 `agent-builder-design.md`
