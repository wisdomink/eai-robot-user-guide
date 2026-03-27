# FF Robot RAG Server

FF Robot 全系列产品的 AI 后端服务，提供多 Agent 智能问答和语义搜索能力。

自托管多 Agent 工作流（Triage + 各产品 Support Agent），聊天流量全部经过后端处理。

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 异步 ASGI，支持 SSE 流式响应 |
| 对话协议 | [OpenAI ChatKit](https://github.com/openai/chatkit-python) | 线程管理、消息持久化、流式传输 |
| AI 推理 | OpenAI Agents SDK + FileSearchTool | 多 Agent 工作流，托管式文档检索 |
| LLM | gpt-5（可通过 `.env` 的 `LLM_MODEL` 切换） | 对话生成 |
| 语义搜索 | OpenAI Vector Store Search API | 跨页面中英文语义搜索 |

## 架构概览

```
用户提问 → ChatKit 协议 → POST /api/chatkit
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

## 项目结构

```
rag_server/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI 入口
│   ├── core/
│   │   └── config.py                # 环境变量 + 路径常量
│   └── services/
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
├── create_vector_store.py           # 同步手册文档到 Vector Store（ROBOT_ALL）
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
- OpenAI Vector Store（各产品独立库 + 全量库，见下方环境变量）

### 1. 创建 / 更新 Vector Store

`create_vector_store.py` 会将 `src/content/pages/` 下所有在 `sidebar.json` 中引用的 Markdown 同步到 **全量** Vector Store（`OPENAI_VECTOR_STORE_ROBOT_ALL_ID`）。语义搜索与该全量库绑定；Backend 模式下各 Support Agent 使用各自产品的 Vector Store ID。

```bash
cd rag_server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 编辑 .env，填入 OPENAI_API_KEY 与各 Vector Store ID
python create_vector_store.py
```

首次需在 OpenAI 控制台创建 Vector Store，将得到的 ID 填入 `.env`。若仅使用语义搜索，可只配置 `OPENAI_VECTOR_STORE_ROBOT_ALL_ID` 并运行上述脚本同步文档。

### 2. 启动服务

**一键启动（推荐）：**

```bash
cd rag_server
chmod +x server_run.sh
./server_run.sh
```

脚本会：检查 Python → 校验 `.env` → 创建/使用虚拟环境 → 安装依赖 → 启动服务。

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

在 `.env` 中配置（参考 `.env.example`）：

### 基础配置

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API 密钥 |
| `LLM_MODEL` | | `gpt-5` | Agent 使用的 LLM 模型 |

### Vector Store

| 变量 | 必填 | 说明 |
|------|:----:|------|
| `OPENAI_VECTOR_STORE_MASTER_ULTRA_ID` | ✅ | Master Ultra 产品文档库 |
| `OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID` | ✅ | Futurist Ultra 产品文档库 |
| `OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID` | ✅ | Aegis Ultra 产品文档库 |
| `OPENAI_VECTOR_STORE_AEGIS_EDU_ID` | ✅ | Aegis EDU 产品文档库 |
| `OPENAI_VECTOR_STORE_ROBOT_ALL_ID` | ✅ | 全量文档库（语义搜索 + General Agent；`create_vector_store.py` 同步目标） |

### 其他

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `PUBLIC_BASE_URL` | | — | 应用公网地址，用于 ChatKit iframe 中图片 URL 重写 |

端口通过 shell 环境变量控制（不在 `.env` 中）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_PORT` | `8000` | 服务监听端口 |

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/chatkit` | POST | ChatKit 协议端点（线程管理 + 流式对话） |
| `/api/search` | GET | 语义搜索（`?q=查询词&limit=10`） |
| `/api/chat-history` | GET | 获取所有对话线程列表（`?limit=50&order=desc`） |
| `/api/chat-history/{thread_id}` | GET | 获取指定线程的消息和 Agent 追踪记录 |
| `/api/post-lead` | POST | 保存一条用户留资数据 |
| `/api/get-leads` | GET | 获取全部留资数据 |
| `/api/get-lead-capture-config` | GET | 获取 Triage 留资触发配置（`recommendations.json` 中 `lead_capture` + `purchase_intent_keywords`） |
| `/api/save-lead-capture-config` | POST | 保存留资 Triage 配置（合并写入 `recommendations.json`，供动态生成 `purchase_intent` 提示词） |
| `/api/get-recommendations` | GET | 获取全部推荐图鉴条目 |
| `/api/save-recommendation` | POST | 按 `id` 保存或更新一条推荐图鉴条目 |
| `/api/delete-recommendation/{recommendation_id}` | DELETE | 删除一条推荐图鉴条目 |
| `/api/logs` | GET | 列出所有可用日志类型及访问链接 |
| `/api/logs/all` | GET | 合并所有日志按时间排序输出（`?tail=200`，每个日志取最后 N 行） |
| `/api/logs/{log_name}` | GET | 获取指定日志的最后 N 行（`?tail=200`，允许：`front.log`、`back.log`、`system.log`） |
| `/health` | GET | 健康检查 |

## 多 Agent 工作流

### Triage Agent（路由预处理）

接收用户输入，输出结构化 JSON：

| 字段 | 说明 |
|------|------|
| `input_lang` | 用户语言：`cn`（中文）/ `en`（英文） |
| `query_type` | 产品路由：`master-ultra` / `futurist-ultra` / `aegis-ultra` / `aegis-edu` / `general` |
| `query_text` | 翻译为英文并扩写后的搜索查询，用于优化 RAG 检索 |

### Support Agent（产品技术支持）

每个产品有独立 Support Agent，使用对应 Vector Store 和 `instructions/*.md` 模板：

| Agent | Vector Store | 文档范围 |
|-------|-------------|---------|
| Master Ultra Support | 独立库 | Master Ultra 手册 |
| Futurist Ultra Support | 独立库 | Futurist Ultra 手册 |
| Aegis Ultra Support | 独立库 | Aegis Ultra 手册 |
| Aegis EDU Support | 独立库 | Aegis EDU 手册 |
| General Support | 全量库 | 全部手册 |

模板支持 `{{input_lang}}`、`{{query_text}}` 等变量插值。

## 引用来源跳转

AI 回答中的引用可点击跳转到对应手册页面：

1. `FileSearchTool` 检索文档后，模型回答包含 `file_citation`
2. `FFRobotConverter` 通过 `sidebar.json` 将文件名映射为页面 slug
3. 输出 `EntitySource`（带 `data.slug`），前端 `entities.onClick` 拦截
4. 前端通过 React Router 执行 SPA 导航

## 评测

内置评测工具用于验证 RAG 回答质量：

```bash
cd rag_server
python -m eval.run_eval                  # 运行全部测试用例
python -m eval.run_eval --ids 1 2 3      # 运行指定用例
python -m eval.run_eval --category safety # 按分类运行
```

## 注意事项

- 手册内容变更后，需重新运行 `create_vector_store.py` 更新全量 Vector Store；Backend 模式下若使用各产品独立库，需在 OpenAI 控制台或自有流程中同步对应库。
- Agent 的 Instructions 模板在 `app/services/instructions/*.md`，修改后重启服务即生效。
- `.env` 含 API Key，已在 `.gitignore` 中排除，切勿提交。
- `venv/` 为 Python 虚拟环境，已在 `.gitignore` 中排除。
