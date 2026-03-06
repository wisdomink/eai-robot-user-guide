# FF Robot RAG Server

基于 RAG（Retrieval-Augmented Generation）的智能问答后端服务，为 FF Master 系列机器人用户手册提供 AI 对话和语义搜索能力。

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 异步 ASGI，支持 SSE 流式响应 |
| 对话协议 | [OpenAI ChatKit](https://github.com/openai/chatkit) | 线程管理、消息持久化、流式传输协议 |
| AI 推理 | OpenAI Agents SDK + File Search | Agent 在代码中定义，使用托管式文档检索 |
| LLM | gpt-5（可通过 `.env` 切换） | 对话回答生成，启用 reasoning |
| 语义搜索 | OpenAI Vector Store Search API | 跨页面语义搜索 |

## 架构概览

```
用户提问
  │
  ▼
┌──────────────────┐
│  FastAPI          │
│  POST /chatkit    │  ← ChatKit 协议（线程/消息/流式）
│  GET  /search     │  ← 语义搜索
└────────┬─────────┘
         │
         ▼
┌──────────────────┐                    ┌─────────────────────┐
│  ChatKit Handler │ ── Agents SDK ──▶  │  OpenAI              │
│  (Bridge Layer)  │    Runner          │  gpt-5               │
│                  │ ◀── Stream ──────  │  + FileSearchTool    │
│  FFRobotConverter│                    │  + Vector Store      │
│  file_citation → │                    │    (文档知识库)       │
│  EntitySource    │                    └─────────────────────┘
└──────────────────┘
```

**核心流程：** 用户提问 → ChatKit 协议解析 → Agents SDK 通过 `FileSearchTool` 自动检索文档 → LLM 基于检索结果生成回答 → `FFRobotConverter` 将 `file_citation` 映射为 `EntitySource`（SPA 可点击引用链接） → 流式 SSE 返回。

## 项目结构

```
rag_server/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 入口：/chatkit、/search、/health
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py              # 路径常量 + 环境变量
│   └── services/
│       ├── __init__.py
│       └── chatkit_handler.py     # Agents SDK Agent 定义 + ChatKit 桥接
├── eval/
│   ├── __init__.py
│   ├── run_eval.py                # RAG 评测脚本（独立使用 Assistants API）
│   └── test_cases.json            # 测试用例
├── create_vector_store.py         # 创建 OpenAI Vector Store 并上传文档
├── create_assistant.py            # [旧方案] 创建 Assistant + Vector Store
├── agent_build_sdk_info           # AgentBuilder 导出的 Agent 定义（TS 参考源）
├── .env                           # 环境变量（API Key 等，勿提交）
├── .env.example                   # 环境变量模板
├── requirements.txt               # Python 依赖
├── server_run.sh                  # 一键启动脚本
└── README.md
```

## 快速开始

### 前置条件

- Python 3.10+
- OpenAI API Key
- OpenAI Vector Store（包含手册文档）

### 1. 创建 Vector Store（首次部署）

```bash
cd rag_server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 填入 OPENAI_API_KEY
python create_vector_store.py
```

脚本会上传用户手册 Markdown 文件到 OpenAI Vector Store，完成后将输出的 `OPENAI_VECTOR_STORE_ID` 填入 `.env`。

### 2. 启动服务

**一键启动（推荐）：**

```bash
cd rag_server
chmod +x server_run.sh
./server_run.sh
```

脚本会自动完成：检查 Python → 校验 `.env` → 创建虚拟环境 → 安装依赖 → 启动服务。

默认端口为 `8000`，可通过环境变量自定义：

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

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API 密钥 |
| `OPENAI_VECTOR_STORE_ID` | ✅ | — | 由 `create_vector_store.py` 生成 |
| `LLM_MODEL` | | `gpt-5` | Agent 使用的 LLM 模型 |

端口通过 shell 环境变量控制（不在 `.env` 中）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_PORT` | `8000` | 服务监听端口 |

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chatkit` | POST | ChatKit 协议端点（线程管理 + 流式对话） |
| `/search` | GET | 语义搜索（`?q=查询词&limit=10`） |
| `/health` | GET | 健康检查 |

## 引用来源跳转

AI 回答中的引用来源支持点击跳转到对应手册页面，实现原理：

1. `FileSearchTool` 检索文档后，模型回答会包含 `file_citation`（引用了哪个文件）
2. `FFRobotConverter` 将 `file_citation` 中的文件名通过 `sidebar.json` 映射为页面 slug
3. 输出 `EntitySource`（而非默认的 `FileSource`），前端 `entities.onClick` 可拦截
4. 前端通过 React Router 执行 SPA 导航到对应页面

## 评测

内置评测工具用于验证 RAG 回答质量（独立使用 Assistants API，需要额外配置 `OPENAI_ASSISTANT_ID`）：

```bash
cd rag_server
python -m eval.run_eval                  # 运行全部测试用例
python -m eval.run_eval --ids 1 2 3      # 运行指定用例
python -m eval.run_eval --category safety # 按分类运行
```

## 注意事项

- 文档变更后需重新运行 `create_vector_store.py` 更新 Vector Store
- Agent 的 Instructions、Model 等配置在代码中定义（`chatkit_handler.py`），修改后需重新部署
- `.env` 文件包含 API Key，已在 `.gitignore` 中排除，切勿手动提交
- `venv/` 目录为 Python 虚拟环境，已在 `.gitignore` 中排除
