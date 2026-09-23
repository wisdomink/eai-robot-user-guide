# FF Robot RAG Server

FF Robot 全系列产品的 AI 后端服务，提供多 Agent 智能问答和语义搜索能力。

当前主流程为自托管 `Plan -> 并行原文检索 -> Output -> Post-Decision`，聊天流量全部经过后端处理。`CHAT_RETRIEVAL_MODE=agent` 可回退到中间检索 Agent；默认 `direct` 直接检索。

点击预置问题时，SDK 传递按钮 ID 和页面范围，后端校验当前配置后直接返回预置答案；自由输入不再使用模糊 FAQ 或历史生成答案缓存。管理页可维护普通按钮的 `reply_text`，留空时兼容既有 FAQ 的精确匹配。答案返回后仍执行推荐判断。详见 [分阶段改造与部署说明](../../docs/rag-chat-migration.md)。

## 说明书按产品同步

使用 `sync_product_rag.py` 预览或替换更新指定产品的独立知识库，并清理符合归属与引用条件的旧文件，详见 [按产品同步说明](RAG_SYNC.md)。默认预览，添加 `--apply` 才修改远程。

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

共享索引路径已就绪：`MANUALS_INDEX_MODE=shared` 时，产品 chat 与网站搜索都读取 `OPENAI_VECTOR_STORE_MANUALS_ID`，按 `MANUALS_RELEASE_MANIFEST` 中的产品生效版本过滤；价格、新闻仍用独立库。新增 `sync_manuals_rag.py` 支持先上传验证、后原子激活，保留旧版本。部署及回滚步骤见 [RAG_SYNC.md](./RAG_SYNC.md#共享-manuals-索引阶段-3)。默认仍为 `legacy`，需完成全部产品索引与清单发布后再切换。Docker 中将清单部署到持久化的 `/app/rag-api/data/manuals-releases.json`。

下面是 `legacy` 模式的旧索引维护方式：

`create_vector_store.py` 会将 `apps/web/src/content/pages/` 下所有在 `sidebar.json` 中引用的 Markdown 同步到 **全量** Vector Store（`OPENAI_VECTOR_STORE_ROBOT_ALL_ID`）。语义搜索会查询该全量库，并合并 Aegis Max 的专属库；后端主流程中的产品 loop pass 使用各自产品的 Vector Store ID。

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
| `OPENAI_VECTOR_STORE_AEGIS_MAX_ID` | ✅ | Aegis Max 产品文档库 |
| `OPENAI_VECTOR_STORE_AEGIS_MEGA_D_ID` | ✅ | FX Aegis Mega D 产品文档库；Agent 路由 key 为 `aegis-mega-d` |
| `OPENAI_VECTOR_STORE_FF91_ID` | ✅ | FF 91 2.0 产品文档库 |
| `OPENAI_VECTOR_STORE_ROBOT_ALL_ID` | ✅ | 全量文档库（语义搜索主库；`create_vector_store.py` 同步目标） |

### 其他

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `PUBLIC_BASE_URL` | | — | 应用公网地址，用于 ChatKit iframe 中图片 URL 重写 |
| `LEADS_FORWARD_URL` | | — | 留资保存成功后，额外同步 POST 到外部 webhook |
| `LEADS_FORWARD_TIMEOUT` | | `10` | 外部 webhook 请求超时（秒） |
| `LEADS_FORWARD_SOURCE` | | `AI Chat` | 外部 webhook payload 中的 `source` 字段 |

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
| `/api/get-homepage-prompts` | GET | 获取首页推荐配置；SDK 传 `?url=https://...` 返回命中页面，管理后台传 `?all=true` 返回全部页面配置 |
| `/api/save-homepage-page` | POST | 整页保存一个首页推荐页面配置（路径、标题、placeholder、info_text、prompts 一次提交） |
| `/api/delete-homepage-page/{page_id}` | DELETE | 删除一个首页推荐页面配置（`pattern=*` 的 fallback 页面不可删除） |
| `/api/logs` | GET | 列出所有可用日志类型及访问链接 |
| `/api/logs/all` | GET | 合并所有日志按时间排序输出（`?tail=200`，每个日志取最后 N 行） |
| `/api/logs/{log_name}` | GET | 获取指定日志的最后 N 行（`?tail=200`，允许：`front.log`、`back.log`、`system.log`） |
| `/health` | GET | 健康检查 |

## 首页推荐配置持久化

首页推荐配置支持两种持久化后端：

- `HOMEPAGE_PROMPTS_BACKEND=file`
  将配置写入 `HOMEPAGE_PROMPTS_DATA_PATH` 指向的 JSON 文件，默认是 `apps/rag-api/data/homepage_prompts.json`。
- `HOMEPAGE_PROMPTS_BACKEND=dynamodb`
  将每个页面配置保存到 `HOMEPAGE_PROMPTS_DDB_TABLE` 指定的 DynamoDB 表中，适合生产环境。

推荐在 AWS 生产环境使用 `dynamodb`，这样镜像重建后配置仍然存在。若必须使用 `file`，则需要为 `/app/data` 或对应路径挂载持久化卷（例如 EFS）。

推荐的环境策略：

- 本地 / 开发：`HOMEPAGE_PROMPTS_BACKEND=file`
- AWS / 生产：`HOMEPAGE_PROMPTS_BACKEND=dynamodb`

仓库中的 `apps/rag-api/data/homepage_prompts.json` 作为默认模板文件保留。生产环境中如需把默认模板同步到线上 DB，可在本地执行同步脚本，由脚本调用线上已部署服务的现有首页推荐 API 逐页更新。

当前 JSON schema 为：

```json
{
  "pages": [
    {
      "id": "www_home",
      "pattern": "https://www.ff.com/",
      "label": "官网首页",
      "greeting": "想了解 FF 的产品吗？",
      "placeholder": "Ask anything about FF...",
      "info_text": "",
      "prompts": [
        {
          "id": "www_home_1",
          "enabled": true,
          "label": "FF 目前有哪些产品线？",
          "prompt": "FF 目前有哪些产品线？",
          "sort_order": 0
        }
      ]
    },
    {
      "id": "fallback",
      "pattern": "*",
      "label": "默认",
      "greeting": "有什么可以帮您？",
      "placeholder": "Ask anything about FF...",
      "info_text": "",
      "prompts": []
    }
  ]
}
```

匹配优先级为：精确 URL > 前缀通配（`https://host/path/*`）> `*` fallback。后端会自动忽略 query string 和 hash，仅使用 `origin + pathname` 做匹配。

管理后台录入 `pattern` 时支持更宽松的写法：

- 只写路径，如 `/fx`、`/preorder/*`，会自动补成 `https://www.ff.com/...`
- 只写域名和路径，如 `robotics.ff.com/fx-aegis`，会自动补成 `https://robotics.ff.com/fx-aegis`

### 默认配置 API 同步脚本

新增脚本：

`apps/rag-api/sync_homepage_prompts.py`

用途：

- 从 `homepage_prompts.json` 读取默认页面配置
- 调用已部署服务的现有 API：
  - `GET /api/get-homepage-prompts?all=true`
  - `POST /api/save-homepage-page`
  - `DELETE /api/delete-homepage-page/{id}`
- 由线上服务把配置写入当前运行 backend（生产通常是 DynamoDB）

支持三种模式：

- `seed-if-empty`：线上 backend 为空时才初始化
- `merge-additive`：只补充缺失 page，不覆盖线上已有 page
- `force-replace`：以 JSON 为准全量覆盖线上配置，并删除多余 page

示例：

```bash
cd apps/rag-api
python sync_homepage_prompts.py \
  --api-base https://robotics-instruction-manual.ff.com \
  --mode merge-additive
```

AWS 部署时只负责把生产环境切到 DynamoDB：

- `HOMEPAGE_PROMPTS_BACKEND=dynamodb`
- `HOMEPAGE_PROMPTS_DDB_TABLE=<app>-homepage-prompts`

默认模板的远程同步由本地脚本手动执行，不由部署脚本自动触发。

### 留资接口请求体

`POST /api/post-lead` 当前接收以下 JSON 字段：

```json
{
  "product": "aegis-ultra",
  "firstName": "Evan",
  "lastName": "Liu",
  "email": "evanliu@ff.com",
  "phone": "6266668888",
  "thread_id": "thread_xxx"
}
```

如果配置了 `LEADS_FORWARD_URL`，服务端在本地文件或 DynamoDB 保存成功后，还会向外部 webhook 同步发送：

```json
{
  "firstName": "Evan",
  "lastName": "Liu",
  "phone": "6266668888",
  "email": "evanliu@ff.com",
  "source": "AI Chat",
  "product": "ff91"
}
```

## Chat 工作流

### Plan

Plan 在处理前获得服务器识别的页面产品，并结合本轮明确型号和会话上下文生成：

| 字段 | 说明 |
| --- | --- |
| `input_lang` | `cn` 或 `en` |
| `query_text` | 通用检索查询 |
| `loop_plan` | 检索项列表，每项包含 agent、product_key 和独立 query_text |
| `clarification_question` | 非空时先追问，停止本轮检索和推荐 |

### 并行检索

`retrieval_service.py` 是 chat 与网站搜索共用的直接检索实现。Chat 保留各产品、价格、新闻的独立库，网站搜索仍使用原 all + Aegis Max 组合，本阶段未迁移数据。

默认 direct 模式返回原文片段、文件 ID、属性、分数和 evidence_id，不运行中间摘要 Agent。保留并发限制、超时、心跳和部分失败降级。缺少库配置属于资料不可用，不是超出服务范围；无结果不能推断参数或步骤。

`CHAT_RETRIEVAL_MODE=agent` 保留原来的中间 Agent 检索方式以供对照。它仅切换检索实现，不回退新的 Plan/Output 提示词。`RETRIEVAL_MAX_RESULTS` 默认 6，`RETRIEVAL_MAX_CHARS_PER_PASS` 默认 18000；每域独立限制，截断片段明确标记。

### Output 与推荐

Output 基于证据生成流式回答，使用 `[[E1_1]]` 等标记引用实际片段。内部标记在流式输出中被隐藏，最终内容带服务端转换的原生引用。推荐/留资判断仍在答案之后执行，判断失败不会丢失已完成答案。

### 引用来源跳转

- 手册来源按产品和原始文件路径映射到 sidebar 页面，使用 EntitySource，沿用前端 SPA 导航回调。
- 新闻使用该片段的元数据或头部原始链接，转换为 URLSource。
- 无页面链接的资料使用 FileSource，仅展示真实文件信息。
- 只有实际引用且 ID 有效的证据会展示引用，不把所有检索命中自动当成答案来源。

Trace 包含检索模式、Plan/检索耗时、首段正文/总耗时、命中文件与分数以及降级状态。尚未进行真实 API 的准确率和性能对照，不能把节点减少直接等同于已测得的提速或成本下降。

## 评测

RAG 评测脚本已迁至仓库 **`tools/eval/`**（与 `apps/rag-api` 解耦，仍通过 `PYTHONPATH` 引用本目录下的 `app.services`）。在仓库根目录：

```bash
cd tools/eval
./run_eval.sh
# 或: python run_eval.py --ids 1 2 3
```

详见 `tools/eval/README.md` 与 `tools/eval/RAG_EVAL_SYSTEM_OVERVIEW.md`。

## 注意事项

- 手册内容变更后，需重新运行 `create_vector_store.py` 更新全量 Vector Store；Backend 模式下若使用各产品独立库，需在 OpenAI 控制台或自有流程中同步对应库。FF Aegis Max 的独立库由 `OPENAI_VECTOR_STORE_AEGIS_MAX_ID` 指定。
- Agent 的 Instructions 模板在 `app/services/instructions/*.md`，修改后重启服务即生效。
- `.env` 含 API Key，已在 `.gitignore` 中排除，切勿提交。
- `venv/` 为 Python 虚拟环境，已在 `.gitignore` 中排除。
