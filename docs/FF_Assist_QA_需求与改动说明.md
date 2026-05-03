# FF Assist：需求说明与涉及改动

本文档汇总与 **FF Assist 预置问答 / 首页推荐 / 聊天快速命中** 相关的业务需求，以及仓库内已做或需配合的文件改动。

---

## 一、需求目标

1. **单一事实来源（SSOT）**  
   预置问答 Markdown 仅以仓库 `input/` 目录为准，不再在 `docs/` 中维护重复副本。

2. **首页推荐（管理后台）**  
   - `apps/rag-api/data/homepage_prompts.json` 的内容需与 **`input/FF_Assist_QA_EN.md`** 对齐：按文档中每个 `##` 小节的 **Path、Greeting** 以及该节内 **前 3 条** `###` 问题生成/更新英文欢迎语与预置问题。  
   - 线上 AWS（DynamoDB）与本地 RAG 服务中的首页推荐配置，需通过既有同步能力做**覆盖式更新**（与团队流程一致时使用 `sync_homepage_prompts.py`）。

3. **聊天中的预置问题「快速命中」**  
   用户点击预置问题或输入相近问题时，由后端的 **Fast Answer**（预置 FAQ + 可选记忆）优先命中；预置条目仍来自 Markdown 解析，路径由 `config.py` 指向 `input/` 下的中英文文件。

---

## 二、数据流简述

| 能力 | 数据文件 | 运行时读取方 |
|------|-----------|----------------|
| 首页推荐（按 URL 的 greeting / chips） | `apps/rag-api/data/homepage_prompts.json`（生产可同步到 DynamoDB） | `HomepagePromptsStorage` + `/api/get-homepage-prompts` 等 |
| 预置 FAQ 快速回答 | `input/FF Assist_QA_CN.md`、`input/FF_Assist_QA_EN.md` | `FastAnswerService` → `parse_preset_faq_markdown` |
| 重复问题记忆（非预置文案源） | `data/answer_memory.jsonl`（可配置） | `FastAnswerService` 记忆层 |

说明：首页推荐 JSON **不是**从 Markdown 在运行时自动读的；更新 EN 文档后需重新执行生成脚本写入 JSON，再按需执行同步脚本推送到远端。

---

## 三、涉及改动的文件

### 配置与部署

| 文件 | 改动说明 |
|------|-----------|
| `apps/rag-api/app/core/config.py` | `PRESET_FAQ_PATH` / 默认 `PRESET_FAQ_PATHS` 指向 `input/FF Assist_QA_CN.md` 与 `input/FF_Assist_QA_EN.md`。 |
| `Dockerfile` | 运行时镜像内预置 FAQ 的 `COPY` 源改为 `input/` 下上述两个文件。 |
| `.dockerignore` | 忽略 `input/**`，并对两个 FAQ 文件名做例外，保证镜像构建上下文包含它们。 |
| `apps/rag-api/.env.example` | 补充说明：本地默认预置 FAQ 路径位于 `input/`。 |

### 已移除（避免与 `input/` 重复）

| 文件 | 说明 |
|------|------|
| `docs/FF Assist 预置问题问答集(CN).md` | 已删除；以 `input/FF Assist_QA_CN.md` 为准。 |
| `docs/FF Assist Preset Q&A Collection (EN).md` | 已删除；以 `input/FF_Assist_QA_EN.md` 为准。 |

### 首页推荐 JSON 与生成脚本

| 文件 | 改动说明 |
|------|-----------|
| `apps/rag-api/data/homepage_prompts.json` | 由 `input/FF_Assist_QA_EN.md` 解析生成，英文 greeting / label / prompt；保留与原配置一致的 **page `id` 与 prompt `id`** 以便同步。 |
| `apps/rag-api/scripts/generate_homepage_prompts_from_en_md.py` | **新增**：从 EN Markdown 生成/覆盖 `homepage_prompts.json`。 |

### 行为修复（与首页 pattern 规范化相关）

| 文件 | 改动说明 |
|------|-----------|
| `apps/rag-api/app/services/homepage_prompts_service.py` | `_normalize_pattern`：对以 `/*` 结尾的通配 URL，避免规范化后出现错误的 `//*`。 |

### 既有脚本（未改逻辑，但与「覆盖更新线上/本地」配套）

| 文件 | 说明 |
|------|------|
| `apps/rag-api/sync_homepage_prompts.py` | 将本地 `homepage_prompts.json` 通过 HTTP API 同步到已部署服务（如 `--mode force-replace` 全量对齐并删除远端多余页等）。 |

### 源内容（编辑入口）

| 文件 | 说明 |
|------|------|
| `input/FF_Assist_QA_EN.md` | 英文预置问答正文 + 与首页区块对应的 Path/Greeting/小节结构；改首页推荐前应先更新此文件并再跑生成脚本。 |
| `input/FF Assist_QA_CN.md` | 中文预置 FAQ，供快速命中与双语场景使用。 |

---

## 四、推荐操作流程（维护人员）

1. 编辑 `input/FF_Assist_QA_EN.md`（及如需中文则编辑 `input/FF Assist_QA_CN.md`）。  
2. 生成首页推荐 JSON：  
   `cd apps/rag-api && python3 scripts/generate_homepage_prompts_from_en_md.py`  
3. 本地验证：启动 RAG API（`file` 后端时直接读 `data/homepage_prompts.json`）。  
4. 同步到线上：  
   `python3 sync_homepage_prompts.py --api-base <部署根 URL> --mode force-replace`（按需配置 `--token` 等）。  
5. 发布包含 `input/` FAQ 与 Dockerfile 变更的镜像/部署，使容器内快速命中使用最新 Markdown。

---

## 五、不在本次范围内的内容

- **Answer memory**（`answer_memory.jsonl`）的清空或批量改写：与首页推荐、预置 Markdown 无直接生成关系，需单独策略或运维操作。  
- **管理后台 UI** 本身未改；仅数据与后端配置路径发生变化。

如需把本说明挪到其它路径或拆成「需求规格 / 变更记录」两份文档，可在仓库内自行复制调整后提交。
