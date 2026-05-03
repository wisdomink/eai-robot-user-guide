# scripts/

本目录统一存放项目维护脚本，均从**仓库根目录**运行。

---

## generate_homepage_prompts.py

从英文预置 Q&A 文档生成后台管理首页配置 JSON。

**数据来源：** `input/FF_Assist_QA_EN.md`  
**写入目标：** `apps/rag-api/data/homepage_prompts.json`

**运行方式：**
```bash
python3 scripts/generate_homepage_prompts.py
```

**使用场景：** 编辑 `input/FF_Assist_QA_EN.md` 后，重新运行本脚本即可更新首页推荐的 greeting 文案和预置问题。脚本会保留已有 page/prompt ID，多次运行安全。

---

## sync_homepage_prompts.py

将本地 `homepage_prompts.json` 同步到已部署的 FF Assist 服务（通过 HTTP API）。

**运行方式：**
```bash
# 默认目标：https://robotics-instruction-manual.ff.com（upsert-all 模式）
python3 scripts/sync_homepage_prompts.py

# 全量对齐：覆盖本地所有页，并删除远端多余页
python3 scripts/sync_homepage_prompts.py --mode force-replace

# 预览 diff，不实际写入
python3 scripts/sync_homepage_prompts.py --dry-run

# 指向其他部署地址
python3 scripts/sync_homepage_prompts.py --api-base https://other-deploy.ff.com
```

**鉴权：** 通过 `--token` 参数或 `FF_API_TOKEN` 环境变量传入 Bearer Token。

| 参数 | 说明 |
|------|------|
| `--api-base` | 部署根 URL（默认 `https://robotics-instruction-manual.ff.com`，或设 `FF_API_BASE` 环境变量） |
| `--mode` | `seed-if-empty` / `merge-additive` / `upsert-all`（默认）/ `force-replace` |
| `--token` | Bearer Token（或 `FF_API_TOKEN` 环境变量） |
| `--dry-run` | 只打印 diff，不发送写请求 |
| `--insecure` | 跳过 TLS 证书验证 |
| `--source` | 覆盖源 JSON 路径（默认 `apps/rag-api/data/homepage_prompts.json`） |

---

## 典型工作流

```
1. 编辑 input/FF_Assist_QA_EN.md
2. python3 scripts/generate_homepage_prompts.py       # 更新本地 JSON
3. 本地启动 RAG API 验证效果
4. python3 scripts/sync_homepage_prompts.py \
       --mode force-replace                           # 推送到线上（默认目标）
```
