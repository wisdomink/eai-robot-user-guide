# FF Robot RAG Server

基于 RAG（Retrieval-Augmented Generation）的智能问答后端服务，为 FF Master 系列机器人用户手册提供 AI 对话能力。

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 异步 ASGI，支持 SSE 流式响应 |
| 对话协议 | [OpenAI ChatKit](https://github.com/openai/chatkit) | 线程管理、消息持久化、流式传输协议 |
| RAG | OpenAI Assistants API + File Search | 托管式文档检索与生成 |
| LLM | gpt-4o-mini（可通过 `.env` 切换） | 对话回答生成 |

## 架构概览

```
用户提问
  │
  ▼
┌──────────────────┐
│  FastAPI          │
│  POST /chatkit    │  ← ChatKit 协议（线程/消息/流式）
└────────┬─────────┘
         │
         ▼
┌──────────────────┐                    ┌─────────────────────┐
│  ChatKit Handler │ ── Assistants ──▶  │  OpenAI              │
│  (Bridge Layer)  │    API             │  Assistant           │
│                  │ ◀── Stream ──────  │  + File Search (RAG) │
└──────────────────┘                    └─────────────────────┘
```

**核心流程：** 用户提问 → ChatKit 协议解析 → Assistants API 自动调用 `file_search` 检索文档 → GPT 基于检索结果生成回答 → 流式 SSE 返回并自动附加引用来源链接。

## 项目结构

```
rag_server/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 入口，定义 /chatkit、/health 端点
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py            # 路径常量 + 环境变量
│   └── services/
│       ├── __init__.py
│       └── chatkit_handler.py   # ChatKit ↔ Assistants API 桥接层
├── eval/
│   ├── __init__.py
│   ├── run_eval.py              # RAG 评测脚本
│   └── test_cases.json          # 测试用例
├── create_assistant.py          # 创建 OpenAI Assistant + Vector Store 的一次性脚本
├── .env                         # 环境变量（API Key 等，勿提交）
├── .env.example                 # 环境变量模板
├── requirements.txt             # Python 依赖
├── server_run.sh                # 一键启动脚本
└── README.md
```

## 快速开始

### 前置条件

- Python 3.10+
- OpenAI API Key

### 1. 创建 Assistant（首次部署）

```bash
cd rag_server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 填入 OPENAI_API_KEY
python create_assistant.py
```

脚本会上传用户手册 Markdown 文件到 OpenAI Vector Store 并创建 Assistant，完成后将输出的 `OPENAI_ASSISTANT_ID` 填入 `.env`。

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
| `OPENAI_ASSISTANT_ID` | ✅ | — | 由 `create_assistant.py` 生成 |
| `LLM_MODEL` | | `gpt-4o-mini` | Assistant 使用的 LLM 模型（仅创建时生效） |

端口通过 shell 环境变量控制（不在 `.env` 中）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_PORT` | `8000` | 服务监听端口 |

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chatkit` | POST | ChatKit 协议端点（线程管理 + 流式对话） |
| `/health` | GET | 健康检查 |

## 评测

内置评测工具用于验证 RAG 回答质量：

```bash
cd rag_server
python -m eval.run_eval                  # 运行全部测试用例
python -m eval.run_eval --ids 1 2 3      # 运行指定用例
python -m eval.run_eval --category safety # 按分类运行
```

## 注意事项

- 文档变更后需重新运行 `create_assistant.py` 更新 Vector Store 和 Assistant
- `.env` 文件包含 API Key，已在 `.gitignore` 中排除，切勿手动提交
- `venv/` 目录为 Python 虚拟环境，已在 `.gitignore` 中排除
