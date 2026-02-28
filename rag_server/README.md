# FF Robot RAG Server

基于 RAG（Retrieval-Augmented Generation）的智能问答后端服务，为 FF Master Ultra Edition 机器人用户手册提供 AI 对话能力。

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 异步 ASGI，支持 SSE 流式响应 |
<<<<<<< HEAD
| 对话协议 | OpenAI ChatKit | 线程管理、消息持久化、流式传输协议 |
| Agent 框架 | OpenAI Agents SDK | Tool 调用、指令遵循、流式推理 |
| 向量数据库 | ChromaDB | 本地持久化，内置 OpenAI embedding |
| LLM | gpt-4o-mini | 对话回答生成 |
| Embedding | text-embedding-3-small | 文档与查询向量化 |
=======
| 对话协议 | [OpenAI ChatKit](https://github.com/openai/chatkit) | 线程管理、消息持久化、流式传输协议 |
| Agent 框架 | [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | Tool 调用、指令遵循、流式推理 |
| 向量数据库 | ChromaDB（本地持久化） | 内置 OpenAI Embedding，余弦相似度检索 |
| LLM | gpt-4o-mini（可通过 `.env` 切换） | 对话回答生成 |
| Embedding | text-embedding-3-small（可通过 `.env` 切换） | 文档与查询向量化 |
>>>>>>> bf40222 (Switching technical solutions, using OpenAI ChatKit for the front end and OpenAI AgentKit for the back end.)

## 架构概览

```
用户提问
  │
  ▼
┌─────────────────┐
│  FastAPI         │
│  POST /chatkit   │  ← ChatKit 协议（线程/消息/流式）
└────────┬────────┘
         │
         ▼
┌─────────────────┐    search_manual()    ┌────────────┐
│  OpenAI Agent   │ ────────────────────▶ │  ChromaDB  │
│  (Agents SDK)   │                       │  向量数据库  │
│                 │ ◀── Top-K 文档块 ──── │            │
└────────┬────────┘                       └────────────┘
         │
         │  检索到的文档 + 用户问题
         ▼
┌─────────────────┐
│  gpt-4o-mini    │  生成带引用的回答（流式 SSE）
└─────────────────┘
```

<<<<<<< HEAD
=======
**核心流程：** 用户提问 → ChatKit 协议解析 → Agent 自动调用 `search_manual` 工具 → ChromaDB 向量检索 Top-K 相关文档块 → Agent 基于检索结果生成回答 → 流式 SSE 返回并自动附加引用来源链接。

>>>>>>> bf40222 (Switching technical solutions, using OpenAI ChatKit for the front end and OpenAI AgentKit for the back end.)
## 项目结构

```
rag_server/
├── app/
<<<<<<< HEAD
│   ├── main.py              # FastAPI 入口，ChatKit 端点
│   ├── core/
│   │   └── config.py        # 配置管理（路径、环境变量）
│   └── services/
│       ├── chatkit_handler.py  # ChatKit Server + Agent + RAG Tool
│       ├── loader.py           # Markdown 文档加载与按标题切分
│       └── rag_engine.py       # ChromaDB 向量索引 + 检索
├── vector_storage/           # ChromaDB 持久化存储（自动生成）
├── .env                      # 环境变量（API Key，勿提交）
├── .env.example              # 环境变量模板
├── requirements.txt          # Python 依赖
├── server_run.sh             # 一键启动脚本
=======
│   ├── __init__.py
│   ├── main.py                # FastAPI 入口，定义 /chatkit、/reindex、/health 端点
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # 路径常量 + 环境变量（OPENAI_API_KEY、模型名等）
│   └── services/
│       ├── __init__.py
│       ├── chatkit_handler.py  # ChatKit Server + Agent 定义 + search_manual RAG Tool
│       ├── loader.py           # sidebar.json 解析 → Markdown 加载 → 按标题切分为 Chunk
│       └── rag_engine.py       # ChromaDB 向量索引构建 + 检索
├── vector_storage/             # ChromaDB 持久化存储（运行时自动生成）
├── venv/                       # Python 虚拟环境（自动创建）
├── .env                        # 环境变量（API Key 等，勿提交）
├── .env.example                # 环境变量模板
├── requirements.txt            # Python 依赖
├── server_run.sh               # 一键启动脚本
>>>>>>> bf40222 (Switching technical solutions, using OpenAI ChatKit for the front end and OpenAI AgentKit for the back end.)
└── README.md
```

## 快速开始

<<<<<<< HEAD
### 一键启动
=======
### 前置条件

- Python 3.10+
- OpenAI API Key

### 一键启动（推荐）

使用 `server_run.sh` 脚本一键完成所有环境准备和启动：
>>>>>>> bf40222 (Switching technical solutions, using OpenAI ChatKit for the front end and OpenAI AgentKit for the back end.)

```bash
cd rag_server
chmod +x server_run.sh
./server_run.sh
```
<<<<<<< HEAD

脚本会自动创建虚拟环境、安装依赖、检查 API Key 并启动服务。

### 手动启动

```bash
cd rag_server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 编辑 .env 填入 OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

首次启动时，服务会自动读取前端项目的 `src/content/pages/*.md` 文件构建向量索引。
=======

脚本会按顺序自动执行以下步骤：

1. **检查 Python 3** — 未安装则提示下载链接并退出
2. **检查 `.env` 文件** — 若不存在，自动从 `.env.example` 拷贝模板并提示填写 API Key
3. **校验 `OPENAI_API_KEY`** — 未设置或仍为占位符则报错退出
4. **创建虚拟环境** — 若 `venv/` 目录不存在，自动运行 `python3 -m venv venv`
5. **安装/更新依赖** — 通过 `requirements.txt` 的 MD5 哈希判断是否需要重新安装，避免重复 `pip install`
6. **启动服务** — 运行 `uvicorn app.main:app --reload --host 0.0.0.0 --port $PORT`

默认端口为 `8000`，可通过环境变量 `RAG_PORT` 自定义：

```bash
RAG_PORT=9000 ./server_run.sh
```

启动成功后会输出：

```
🚀 启动 ChatKit RAG Server (port 8000)
   ChatKit 端点: http://localhost:8000/chatkit
   健康检查:     http://localhost:8000/health
   LLM 模型:     gpt-4o-mini
```

### 手动启动

如需更多控制，可手动完成环境配置和启动：

```bash
cd rag_server

# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY

# 启动服务（--reload 开启热重载）
uvicorn app.main:app --reload --port 8000
```

## 环境变量

在 `.env` 文件中配置（参考 `.env.example`）：

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API 密钥 |
| `LLM_MODEL` | | `gpt-4o-mini` | 对话生成使用的 LLM 模型 |
| `EMBEDDING_MODEL` | | `text-embedding-3-small` | 文档向量化使用的 Embedding 模型 |
| `SIMILARITY_TOP_K` | | `5` | 向量检索返回的最相似文档块数量 |

端口通过 shell 环境变量控制（不在 `.env` 中）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_PORT` | `8000` | 服务监听端口 |
>>>>>>> bf40222 (Switching technical solutions, using OpenAI ChatKit for the front end and OpenAI AgentKit for the back end.)

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chatkit` | POST | ChatKit 协议端点（线程管理 + 流式对话） |
<<<<<<< HEAD
| `/reindex` | POST | 强制重建向量索引 |
=======
| `/reindex` | POST | 强制重建向量索引（文档变更后调用） |
>>>>>>> bf40222 (Switching technical solutions, using OpenAI ChatKit for the front end and OpenAI AgentKit for the back end.)
| `/health` | GET | 健康检查 |

## 数据处理流程

### 文档索引（启动时 / reindex 时）

```
<<<<<<< HEAD
sidebar.json → 解析页面列表（section_id, slug, file）
=======
sidebar.json → parse_sidebar() 解析页面列表
  每个页面包含: section_id, section_title, page_title, slug, file
>>>>>>> bf40222 (Switching technical solutions, using OpenAI ChatKit for the front end and OpenAI AgentKit for the back end.)
     │
     ▼
src/content/pages/*.md → 读取 Markdown 内容
     │
     ▼
<<<<<<< HEAD
按 H1-H3 标题切分为文档块（chunk）
每个 chunk 携带: page_title, section_id, url_path, header_path, heading_anchor
     │
     ▼
ChromaDB 内置 OpenAI Embedding → 向量化 → 持久化存储
=======
_split_markdown_by_headers() 按 H1-H3 标题切分为 Chunk
  每个 Chunk 携带 metadata:
    file_path, page_title, section_id, section_title,
    url_path, header_path, heading_anchor
     │
     ▼
ChromaDB OpenAI Embedding → 批量向量化（batch_size=100）→ 持久化存储
>>>>>>> bf40222 (Switching technical solutions, using OpenAI ChatKit for the front end and OpenAI AgentKit for the back end.)
```

### 用户查询

```
<<<<<<< HEAD
用户 query → ChatKit 协议解析 → Agent 调用 search_manual Tool
=======
用户 query → ChatKit 协议解析 → Agent 自动调用 search_manual Tool
     │
     ▼
ChromaDB 余弦相似度搜索 → Top-K 文档块 + 元数据
>>>>>>> bf40222 (Switching technical solutions, using OpenAI ChatKit for the front end and OpenAI AgentKit for the back end.)
     │
     ▼
Agent (LLM) 基于检索内容生成中文回答
     │
     ▼
<<<<<<< HEAD
Agent (gpt-4o-mini) 基于检索内容生成回答
     │
     ▼
流式 SSE 返回 + 引用来源注解（含精确锚点 URL）
=======
流式 SSE 返回 + 自动附加参考来源（含精确锚点 URL，如 /page#section-name）
>>>>>>> bf40222 (Switching technical solutions, using OpenAI ChatKit for the front end and OpenAI AgentKit for the back end.)
```

## 注意事项

- **首次启动**会自动构建索引，耗时取决于文档数量和 Embedding API 速度
<<<<<<< HEAD
- **后续启动**会复用已有的 ChromaDB 数据，无需重新构建
- **Markdown 文件变更后**需要调用 `POST /reindex` 更新索引
- `.env` 文件包含 API Key，切勿提交到版本控制
=======
- **后续启动**会复用已有的 ChromaDB 数据（`vector_storage/`），无需重新构建
- **Markdown 文件变更后**需调用 `POST /reindex` 更新索引
- `.env` 文件包含 API Key，已在 `.gitignore` 中排除，切勿手动提交
>>>>>>> bf40222 (Switching technical solutions, using OpenAI ChatKit for the front end and OpenAI AgentKit for the back end.)
- `vector_storage/` 目录为自动生成的本地向量数据库，可安全删除后重建
- `venv/` 目录为 Python 虚拟环境，已在 `.gitignore` 中排除
- Agent 的系统指令要求必须先调用 `search_manual` 搜索文档后再回答，仅基于检索结果作答
