# RAG 评测（`tools/eval`）

本目录可**在仓库根目录下独立运行**，通过 `sys.path` 引用 `apps/rag-api`，直接调用生产 ChatKit respond 流程（Plan → 并行检索 → Output → Post-Decision），避免维护另一套编排。返回给 Judge 的答案包含实际引用的来源。

## 前置条件

- Python 3.10+，并已安装 `tools/eval/requirements.txt` 与 `apps/rag-api/requirements.txt` 中所需依赖（评测脚本会 `import app.services.*`）。
- 配置 `OPENAI_API_KEY` 及 Vector Store 相关环境变量（见 `run_eval.py` 顶部说明）。

## 环境变量加载顺序

1. `tools/eval/.env`（若存在）
2. 仓库根目录 `.env`
3. `apps/rag-api/.env`
4. 否则由 `load_dotenv()` 默认查找

## 运行

在**仓库根目录**下：

```bash
cd tools/eval
./run_eval.sh
# 或
python run_eval.py --ids 1 2 3
```

分析评测报告：

```bash
./analyze_eval.sh
```

同一题库对照检索实现（需要真实 API，产生检索及模型调用费用）：

```bash
CHAT_RETRIEVAL_MODE=direct apps/rag-api/venv/bin/python tools/eval/run_eval.py --ids 1 2 3 --report /tmp/rag-direct.json
CHAT_RETRIEVAL_MODE=agent apps/rag-api/venv/bin/python tools/eval/run_eval.py --ids 1 2 3 --report /tmp/rag-agent.json
```

以上命令从仓库根目录运行。仅比较检索实现，两个模式都使用当前 Plan/Output 提示词；不是完整旧版本基线。评测报告包含 retrieval_mode，控制台打印实际 chat trace 的首段正文/总耗时。当前交付仅完成离线回归，尚未运行上述联网对照。

更完整的说明见 `RAG_EVAL_SYSTEM_OVERVIEW.md`、`RAG_EVAL_TECH_DOC.md`。
