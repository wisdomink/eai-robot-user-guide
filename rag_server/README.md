# FF Robot RAG Server

基于 RAG（Retrieval-Augmented Generation）的智能问答后端服务，为 FF Master Ultra Edition 机器人用户手册提供 AI 对话能力。

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 异步 ASGI，支持 SSE 流式响应 |
| 对话协议 | OpenAI ChatKit | 线程管理、消息持久化、流式传输协议 |
| Agent 框架 | OpenAI Agents SDK | Tool 调用、指令遵循、流式推理 |
| 向量数据库 | ChromaDB | 本地持久化，内置 OpenAI embedding |
| LLM | gpt-4o-mini | 对话回答生成 |
| Embedding | text-embedding-3-small | 文档与查询向量化 |

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

## 项目结构

```
rag_server/
├── app/
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
└── README.md
```

## 快速开始

### 一键启动

```bash
cd rag_server
chmod +x server_run.sh
./server_run.sh
```

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

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chatkit` | POST | ChatKit 协议端点（线程管理 + 流式对话） |
| `/reindex` | POST | 强制重建向量索引 |
| `/health` | GET | 健康检查 |

## 数据处理流程

### 文档索引（启动时 / reindex 时）

```
sidebar.json → 解析页面列表（section_id, slug, file）
     │
     ▼
src/content/pages/*.md → 读取 Markdown 内容
     │
     ▼
按 H1-H3 标题切分为文档块（chunk）
每个 chunk 携带: page_title, section_id, url_path, header_path, heading_anchor
     │
     ▼
ChromaDB 内置 OpenAI Embedding → 向量化 → 持久化存储
```

### 用户查询

```
用户 query → ChatKit 协议解析 → Agent 调用 search_manual Tool
     │
     ▼
ChromaDB 余弦相似度搜索 → Top-K 文档块
     │
     ▼
Agent (gpt-4o-mini) 基于检索内容生成回答
     │
     ▼
流式 SSE 返回 + 引用来源注解（含精确锚点 URL）
```

## 注意事项

- **首次启动**会自动构建索引，耗时取决于文档数量和 Embedding API 速度
- **后续启动**会复用已有的 ChromaDB 数据，无需重新构建
- **Markdown 文件变更后**需要调用 `POST /reindex` 更新索引
- `.env` 文件包含 API Key，切勿提交到版本控制
- `vector_storage/` 目录为自动生成的本地向量数据库，可安全删除后重建
