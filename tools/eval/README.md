# RAG 评测（`tools/eval`）

本目录可**在仓库根目录下独立运行**，通过 `sys.path` 引用 `apps/rag-api` 中的 `app.services`（与线上一致的 Plan → Loop → Output 逻辑）。

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

更完整的说明见 `RAG_EVAL_SYSTEM_OVERVIEW.md`、`RAG_EVAL_TECH_DOC.md`。
