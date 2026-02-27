# FF Robot RAG Server

基于 RAG（Retrieval-Augmented Generation）的智能问答后端服务，为 FF Master Ultra Edition 机器人用户手册提供 AI 对话能力。

## 架构概览

```
用户提问
  │
  ▼
┌─────────────┐    query embedding    ┌────────────┐
│  FastAPI     │ ──────────────────▶  │  ChromaDB  │
│  /chat       │                      │  向量数据库  │
│  /chat/sync  │  ◀── Top-K 文档块 ── │            │
└──────┬───────┘                      └────────────┘
       │
       │  检索到的文档 + 用户问题
       ▼
┌─────────────┐
│  LLM        │  生成带引用标注的回答
│  (GPT/Gemini)│
└─────────────┘
```

### 两个模型各司其职

| 模型 | 类型 | 作用 | 调用时机 |
|------|------|------|----------|
| `text-embedding-3-small` | Embedding 模型 | 将文本转为高维向量 | 建索引时（每个文档块）+ 每次用户提问时 |
| `gpt-4o-mini` | LLM | 阅读检索到的文档，生成结构化回答 | 用户提问时，检索完成后 |

## 项目结构

```
rag_server/
├── app/
│   ├── main.py              # FastAPI 入口，定义路由和 SSE 流式接口
│   ├── core/
│   │   └── config.py        # 配置管理（路径、模型、环境变量）
│   └── services/
│       ├── loader.py         # Markdown 文档加载与按标题切分
│       └── rag_engine.py     # RAG 引擎：向量索引 + 检索 + LLM 问答
├── vector_storage/           # ChromaDB 持久化存储（自动生成，已 gitignore）
├── .env                      # 环境变量（API Key 等，勿提交）
├── .env.example              # 环境变量模板
├── requirements.txt          # Python 依赖
└── README.md
```

## 快速开始

### 1. 创建虚拟环境

```bash
cd rag_server
python3 -m venv venv
source venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key：

```env
# 选择 LLM 提供商：openai 或 gemini
LLM_PROVIDER=openai

# OpenAI 配置
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

# Google Gemini 配置（当 LLM_PROVIDER=gemini 时生效）
GOOGLE_API_KEY=your-google-api-key-here
GEMINI_LLM_MODEL=models/gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004

# RAG 检索参数
SIMILARITY_TOP_K=5
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

首次启动时，服务会自动读取前端项目的 `src/content/pages/*.md` 文件，构建向量索引。

## API 接口

### `POST /chat` — 流式问答（SSE）

```bash
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "如何给机器人充电？"}'
```

返回 Server-Sent Events 流，包含三种事件类型：

```
data: {"type": "token", "content": "根据"}
data: {"type": "token", "content": "说明书"}
...
data: {"type": "sources", "sources": [{"title": "...", "url_path": "...", ...}]}
data: {"type": "done"}
```

### `POST /chat/sync` — 同步问答

```bash
curl -X POST http://localhost:8000/chat/sync \
  -H "Content-Type: application/json" \
  -d '{"query": "如何给机器人充电？"}'
```

返回完整 JSON 响应：

```json
{
  "answer": "根据说明书 [1]，充电步骤如下...",
  "sources": [
    {
      "title": "充电指南",
      "section": "基本操作",
      "header_path": "充电指南 > 充电步骤",
      "url_path": "/charging",
      "file_path": "charging.md"
    }
  ]
}
```

### `POST /reindex` — 重建索引

当 Markdown 文件内容发生变化后，调用此接口强制重建向量数据库：

```bash
curl -X POST http://localhost:8000/reindex
```

### `GET /health` — 健康检查

```bash
curl http://localhost:8000/health
```

## 数据处理流程

### 文档索引（启动时 / reindex 时）

```
sidebar.json → 解析页面列表
     │
     ▼
src/content/pages/*.md → 读取 Markdown 内容
     │
     ▼
按 H1-H3 标题切分为文档块（chunk）
     │
     ▼
每个 chunk 携带元数据：page_title, section_title, url_path, header_path
     │
     ▼
Embedding 模型 → 转为向量 → 存入 ChromaDB
```

### 用户查询

```
用户 query
     │
     ▼
Embedding 模型 → query 向量
     │
     ▼
ChromaDB 余弦相似度搜索 → Top-K 文档块
     │
     ▼
System Prompt + 文档上下文 + 用户问题 → LLM
     │
     ▼
生成带 [1][2] 引用标注的回答 + 参考来源列表
```

## 注意事项

- **首次启动**会自动构建索引，耗时取决于文档数量和 Embedding API 速度
- **后续启动**会复用已有的 ChromaDB 数据，无需重新构建
- **Markdown 文件变更后**需要手动调用 `POST /reindex` 更新索引
- `.env` 文件包含 API Key，切勿提交到版本控制
- `vector_storage/` 目录为自动生成的本地向量数据库，可安全删除后重建
