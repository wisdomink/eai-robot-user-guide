# FF Robot RAG Server

FF Robot 全系列产品的 AI 后端服务，提供多 Agent 智能问答和语义搜索能力。

当前主流程为自托管 `plan -> loop -> output -> recommendation` 多 Agent 工作流，聊天流量全部经过后端处理。

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI + Uvicorn | 异步 ASGI，支持 SSE 流式响应 |
| 对话协议 | [OpenAI ChatKit](https://github.com/openai/chatkit-python) | 线程管理、消息持久化、流式传输 |
| AI 推理 | OpenAI Agents SDK + FileSearchTool | 多 Agent 工作流，托管式文档检索 |
| LLM | gpt-5（可通过 `.env` 的 `LLM_MODEL` 切换） | 对话生成 |
| 语义搜索 | OpenAI Vector Store Search API | 跨页面中英文语义搜索 |

## 架构概览

```text
用户提问 → ChatKit 协议 → POST /api/chatkit
                              │
                    ┌─────────▼──────────┐
                    │    Plan Agent       │  非流式，JSON 输出
                    │  语言/产品/领域识别  │  → product_types
                    │  查询扩写/领域标记    │  → needs_product/price/news
                    └─────────┬──────────┘
                              │ 服务端编排
                 ┌────────────▼────────────┐
                 │       Loop Passes        │  非流式，多轮检索
                 │  Product / Price / News  │  → 结构化检索结果 + 来源
                 └────────────┬────────────┘
                              ▼
                    ┌─────────▼──────────┐
                    │   Output Agent      │  流式最终回答
                    │ 汇总/去重/冲突消解   │
                    └─────────┬──────────┘
                              ▼
                    FFRobotConverter
                    + FinalSourceAppender
                    file_citation / 来源 → EntitySource(slug)
                              │
                    _EventStreamRewriter
                    /images/... → 绝对 URL
                              │
                    SSE 流式返回 → 前端 ChatPanel
```

## 项目结构

```
apps/rag-api/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI 入口
│   ├── core/
│   │   └── config.py                # 环境变量 + 路径常量
│   └── services/
│       ├── chatkit_handler.py       # 多 Agent 工作流 + ChatKit 桥接
│       └── instructions/            # Agent Prompt 模板
│           ├── plan.md              # Plan Agent — 路由预处理
│           ├── product-master.md    # FF Master Product Agent 提示词
│           ├── product-futurist.md  # FF Futurist Product Agent 提示词
│           ├── product-futurist-ultra.md # FF Futurist Ultra Product Agent 提示词
│           ├── product-aegis.md     # FF Aegis Product Agent 提示词
│           ├── product-aegis-ultra.md # FF Aegis Ultra Product Agent 提示词
│           ├── product-ff91.md      # FF 91 2.0 Product Agent 提示词
│           ├── price-agent.md       # FF Price Agent 提示词
│           ├── news-agent.md        # FF News Agent 提示词
│           ├── output.md            # 最终汇总输出提示词
│           ├── general.md           # 历史遗留文件，当前主流程未使用
│           └── fallback.md          # Fallback Agent 中间结果提示词
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

`create_vector_store.py` 会将 `apps/web/src/content/pages/` 下所有在 `sidebar.json` 中引用的 Markdown 同步到 **全量** Vector Store（`OPENAI_VECTOR_STORE_ROBOT_ALL_ID`）。语义搜索与该全量库绑定；后端主流程中的产品 loop pass 使用各自产品的 Vector Store ID。

```bash
cd apps/rag-api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 编辑 .env，填入 OPENAI_API_KEY 与各 Vector Store ID
python create_vector_store.py
```

首次需在 OpenAI 控制台创建 Vector Store，将得到的 ID 填入 `.env`。若仅使用语义搜索，可只配置 `OPENAI_VECTOR_STORE_ROBOT_ALL_ID` 并运行上述脚本同步文档。

### 2. 启动服务

**一键启动（推荐）：**

```bash
cd apps/rag-api
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
cd apps/rag-api
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
| `OPENAI_VECTOR_STORE_MASTER_ID` | ✅ | Master 系列产品文档库（含 Master / Master EDU / Master Ultra） |
| `OPENAI_VECTOR_STORE_FUTURIST_ID` | ✅ | Futurist 产品文档库 |
| `OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID` | ✅ | Futurist Ultra 产品文档库 |
| `OPENAI_VECTOR_STORE_AEGIS_ID` | ✅ | Aegis 系列产品文档库（含 Aegis / Aegis Pro / Aegis EDU） |
| `OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID` | ✅ | Aegis Ultra 产品文档库 |
| `OPENAI_VECTOR_STORE_FF91_ID` | ✅ | FF 91 2.0 产品文档库 |
| `OPENAI_VECTOR_STORE_ROBOT_ALL_ID` | ✅ | 全量文档库（语义搜索；`create_vector_store.py` 同步目标） |

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

### Plan Agent（路由预处理）

接收用户输入，输出结构化 JSON：

| 字段 | 说明 |
|------|------|
| `input_lang` | 用户语言：`cn`（中文）/ `en`（英文） |
| `query_type` | 产品主路由：`master` / `futurist` / `futurist-ultra` / `aegis` / `aegis-ultra` / `ff91` / `""` |
| `query_text` | 翻译为英文并扩写后的搜索查询，用于优化 RAG 检索 |
| `product_types` | 需要检索的产品手册 key 列表；后端会按元素逐轮执行 product loop |
| `needs_product` / `needs_price` / `needs_news` | 控制后端是否执行产品、价格、新闻 loop；若都为 `no`，后端进入兜底模块 |

### Loop Agents（检索子模块）

后端根据 Plan 结果执行 1-N 轮 loop。产品、价格、新闻 loop 均使用 `instructions/*.md` 模板；仅当没有命中任何领域时，进入无工具兜底模块。

| Loop 类型 | Vector Store | 说明 |
|----------|-------------|------|
| Product | 各产品独立库 | 产出结构化检索结果，供 Output Agent 汇总 |
| Price | 价格库 | 提取价格、报价、币种、条款等信息 |
| News | 新闻库 | 提取动态、公告、时间线、最近状态 |
| Fallback Guard | 无 | 生成兜底说明中间结果，不做检索 |

### Output Agent（最终回答）

Output Agent 不做新的 `file_search`，只接收 loop 结果，负责汇总、去重、冲突消解，并流式生成最终回答。最终来源会由 `FFRobotConverter` 和后处理逻辑转换成前端可点击的 `EntitySource`。

## 引用来源跳转

AI 回答中的引用可点击跳转到对应手册页面：

1. `FileSearchTool` 检索文档后，模型回答包含 `file_citation`
2. `FFRobotConverter` 通过 `sidebar.json` 将文件名映射为页面 slug
3. 输出 `EntitySource`（带 `data.slug`），前端 `entities.onClick` 拦截
4. 前端通过 React Router 执行 SPA 导航

## 评测

RAG 评测脚本已迁至仓库 **`tools/eval/`**（与 `apps/rag-api` 解耦，仍通过 `PYTHONPATH` 引用本目录下的 `app.services`）。在仓库根目录：

```bash
cd tools/eval
./run_eval.sh
# 或: python run_eval.py --ids 1 2 3
```

详见 `tools/eval/README.md` 与 `tools/eval/RAG_EVAL_SYSTEM_OVERVIEW.md`。

## 注意事项

- 手册内容变更后，需重新运行 `create_vector_store.py` 更新全量 Vector Store；Backend 模式下若使用各产品独立库，需在 OpenAI 控制台或自有流程中同步对应库。
- Agent 的 Instructions 模板在 `app/services/instructions/*.md`，修改后重启服务即生效。
- `.env` 含 API Key，已在 `.gitignore` 中排除，切勿提交。
- `venv/` 为 Python 虚拟环境，已在 `.gitignore` 中排除。
