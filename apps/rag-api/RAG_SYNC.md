# 按产品同步说明书 RAG

`sync_product_rag.py` 只写指定产品的独立库。没有 `--target`、`--all-store-id` 或 `--replace-legacy` 参数，也不更新搜索总库。默认预览；`--apply` 才修改远程。

## 使用

从仓库根目录执行：

```bash
# 仅校验本地 Markdown
apps/rag-api/venv/bin/python apps/rag-api/sync_product_rag.py --product aegis-max --local-only

# 预览上传、保留、删除旧关联及文件清理资格
apps/rag-api/venv/bin/python apps/rag-api/sync_product_rag.py --product aegis-max --dry-run

# 更新产品库：先上传新版，全部索引完成，再删除旧关联
apps/rag-api/venv/bin/python apps/rag-api/sync_product_rag.py --product aegis-max --apply
```

默认读取 `apps/rag-api/.env`，其中值覆盖同名 shell 环境变量。需要 `OPENAI_API_KEY` 和产品库变量，如 `OPENAI_VECTOR_STORE_AEGIS_MAX_ID`；其他产品按大写 ID、连字符变下划线推导。可用 `--env-file` 指定环境，`--product-store-id` 显式指定库。配置中若目标 ID 同时属于总库或其他产品，脚本拒绝执行。

`--create-product-store` 在没有配置产品库时允许创建；预览不创建。创建前检查同名库，发现已有库则停止并列出 ID；创建请求关闭自动重试。创建 ID 输出并写入报告，不自动修改服务端配置。重试前必须保存该 ID，避免重复创建。Mega D 已接入后端产品 Agent，路由 key 为 `aegis-mega-d`，使用 `OPENAI_VECTOR_STORE_AEGIS_MEGA_D_ID`；同步该库后无需更新 All 即可供 Agent 检索。

本地唯一内容来源是 `apps/web/src/content/sidebar.json` 引用的产品 Markdown。不会读取 DOCX。`--content-dir` 可覆盖目录，`--base-url` 可将根路径 Markdown 链接转换成绝对链接；每次同步应保持域名一致。不会上传图片或识别图中文字。

## 替换与清理

- 当前产品库以本地章节清单为完整内容来源。未变的受管文件复用，其余旧关联（包括旧 PDF、手动上传文件、已删除章节、重复版本）默认移除。
- 如果远程文件属性明确属于其他产品，拒绝操作，不将混合库当成产品库清空。
- 全部新文件索引完成后，再读取远程状态，确认本地每个章节有可用版本且远程文件集合没有意外变化，才删除旧关联。
- 新版脚本上传的文件记录在本地所有权账本中，专供此同步流程使用。旧关联移除并完成库校验后，遍历 API 凭据可见的所有向量库检查候选文件引用。仍有引用的保留；扫描失败则跳过全部全局删除。
- 只有有本地所有权记录且没有向量库引用的候选文件才调用 Files 删除。历史上传文件（包括旧版脚本上传的文件）没有本账本所有权证据，只解除关联并记录，绝不凭文件名自动全局删除。
- 扫描仅覆盖向量库，不证明文件没有被消息、线程、其他工具或外部程序引用。不要将此脚本创建的文件 ID 用于其他用途。若需要共享到非向量库用途，应先改变文件生命周期管理方案。

## 状态与重试

报告：`.logs/rag-sync-<时间戳>.json`，可用 `--report` 指定。

持久账本：`.logs/rag-sync-state/<库ID的哈希>.json`，可用 `--state-dir` 指定。记录已创建文件、待清理 ID、保留的历史文件。**不要当普通日志删除；部署时应放在持久目录并备份。** 丢失账本会失去自动全局清理资格，脚本倾向保留文件。

同一状态目录、同一库使用本地文件锁。不同电脑或不同状态目录不共享锁，请指定唯一同步执行端。Python 使用 `fcntl`，适用于 macOS/Linux。

旧关联删除前先持久化清理队列；删除失败、仍被引用或引用扫描失败的文件保留在队列，下一次 `--apply` 重试。不会从旧版执行报告自动导入所有权。上传返回前断线或返回后尚未成功记录账本时，仍可能留下无法自动追踪的孤立文件。

退出码：

- `0`：预览/本地校验完成，或产品库同步及符合条件的清理完成；历史保留文件仍可能存在。
- `1`：执行失败，查看报告。已执行的远程修改不自动回滚。
- `2`：产品库已验证，但全局清理有待处理项。

## 风险与限制

1. 本地 sidebar 误删章节会变成远程删除；非空校验不能识别内容不完整。
2. 产品库内手动维护的补充资料也会移除。只应指向专用说明书库。
3. 配置检查不能识别所有人为错误，尤其是未在环境变量中登记、也没有产品属性的错误目标库。
4. 引用检查和全局删除之间不是原子操作；另一个进程若同时添加引用，仍可能受影响。本地锁不能约束外部系统。
5. 全局 Files 删除不可撤销，且影响所有引用；没有自动备份或回滚。来源 Markdown 应纳入版本控制。
6. 上传阶段新旧版本短暂共存，删除后检索也可能有延迟；元数据验证不等于真实问答测试。
7. 本脚本不再更新/清理总库。之前上传到总库的 Max 数据仍在，网站跨库搜索仍可能命中那些资料。
8. API 及文件系统写入存在不可原子化的故障窗口。进程中断后应先预览、检查报告，再重试。

## 测试

```bash
apps/rag-api/venv/bin/python -m unittest discover -s apps/rag-api/tests -p test_sync_product_rag.py -v
```

测试使用模拟 API，不修改线上数据。

## 超时和校验诊断

读写超时默认 600 秒，可用 `--request-timeout` 调整；连接超时 30 秒。报告记录上传、关联、索引和创建阶段，以及异常类型和底层异常类型。超时并不能证明服务端未执行请求，应检查报告和现有库后再重试。

删除旧关联后的校验最多进行 6 次，每次间隔 2 秒（API 请求耗时另计），只读不修复。报告的 `verification` 保存每次远程快照和剩余差异；持续不一致时停止，跳过全局文件清理。

## 共享 manuals 索引（阶段 3）

共享库使用 **`sync_manuals_rag.py`**；不要用上面的独立库替换脚本操作它。源文件仍为 sidebar 引用的 Markdown。每个章节携带 product_id、source_path、page_slug、language、content_hash、release_id、managed_by。版本按整个产品计算，章节改变时新建该产品完整版本；从清单移除的章节不会进入新版。旧版留存会增加存储量，清理留到迁移确认之后。

从仓库根目录执行（这些是上线步骤，本次仅执行了 local-only）：

```bash
# 1. 本地完整清单校验，不访问 OpenAI
apps/rag-api/venv/bin/python apps/rag-api/sync_manuals_rag.py --all --local-only

# 2. 首次创建独立 manuals 库并上传验证，不激活
# 要求 .env 中 OPENAI_VECTOR_STORE_MANUALS_ID 为空且目标 manifest 尚不存在
apps/rag-api/venv/bin/python apps/rag-api/sync_manuals_rag.py --all --apply --create-store

# 3. 将报告中的 ID 保存为 .env 的 OPENAI_VECTOR_STORE_MANUALS_ID
# 再次运行会复用已完成的版本。全量校验与搜索探测成功后激活清单
apps/rag-api/venv/bin/python apps/rag-api/sync_manuals_rag.py --all --apply --activate

# 4. 后续按产品预览 / 更新，不影响其他产品
apps/rag-api/venv/bin/python apps/rag-api/sync_manuals_rag.py --product aegis-max
apps/rag-api/venv/bin/python apps/rag-api/sync_manuals_rag.py --product aegis-max --apply --activate
```

脚本读取 `.env`（覆盖 shell 同名变量）；支持 `--env-file`、`--store-id`、`--manifest`、`--report`、`--content-dir`、`--base-url`、`--language`。默认清单为 `apps/rag-api/data/manuals-releases.json`，报告位于 `.logs/manuals-sync-*.json`。源内容是英文，language 默认 en；语言和 base-url 应保持一致，改变它们也会生成新版本。

`--apply` 只暂存；`--activate` 必须与 `--apply` 一起使用。发布前检查全部章节 completed、元数据一致、没有重复版本关联，随后带版本过滤执行搜索探测。一次发布选择的所有产品验证成功才更新清单。单产品第一次激活只产生部分清单，服务端 shared 模式要求清单覆盖 sidebar 全部产品，初次迁移使用 `--all`。默认预览仅进行远程读取，但会写本地报告和锁文件。

上传前后通过报告记录新 Files ID；关联或索引失败不改生效清单，不自动删除孤立 Files。相同版本有 failed / in_progress / 重复或元数据冲突时停止；in_progress 可完成后重试，其他情况先核对报告和远程状态。创建库请求不自动重试，已有名为 manuals 的库会拒绝再次创建；请求结果不明确时先检查控制台，再用明确 ID 继续。

该脚本完全不调用 Files 删除或向量库关联删除。它拒绝把 `.env` 中已有的产品、all、价格、新闻库 ID 当作共享目标。所有写入方必须使用相同清单路径和文件锁；锁只协调同一文件系统，不支持从不同机器同时发布同一库。不要手工修改已发布版本的元数据或关联。

切换服务读取配置：

```dotenv
MANUALS_INDEX_MODE=shared
OPENAI_VECTOR_STORE_MANUALS_ID=vs_新共享库ID
MANUALS_RELEASE_MANIFEST=/app/rag-api/data/manuals-releases.json
CHAT_RETRIEVAL_MODE=direct
```

先把已验证的清单部署到服务端持久化目录，再修改配置并重启。Docker 已声明 `/app/rag-api/data` 数据卷，但不会自动复制本地清单。多实例应部署完全相同的清单和库 ID；一次请求固定读取一个版本快照，之后的请求可看到新清单。清单不完整或库 ID 不符时停止产品检索，不混入 legacy 数据。价格和新闻配置不变。

每次实际激活变更前备份旧清单为同目录 `manuals-releases.previous.json`，重复激活同一版本不覆盖备份。回退最近版本时，在没有同步发布任务运行的情况下，原子替换生效清单（以下路径为容器默认值）：

```bash
cp /app/rag-api/data/manuals-releases.previous.json /app/rag-api/data/manuals-releases.rollback.tmp
mv /app/rag-api/data/manuals-releases.rollback.tmp /app/rag-api/data/manuals-releases.json
```

首次激活没有 previous 备份。需回退整个索引架构时，将 `MANUALS_INDEX_MODE=legacy` 并重启，保留原产品与 ROBOT_ALL 配置即可。旧库及旧共享版本均未被本脚本删除。实际效果、费用、索引可用性和多实例发布仍需阶段 4 联网验收。
