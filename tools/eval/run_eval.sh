#!/usr/bin/env bash
#
# FF Robot RAG 评测启动脚本
#
# 用法:
#   ./run_eval.sh                        # 完整评测（164 个用例）
#   ./run_eval.sh --ids 1 2 3            # 指定用例
#   ./run_eval.sh --category safety      # 按分类
#   ./run_eval.sh --question-type user_rewrite  # 按问题类型
#   ./run_eval.sh --no-triage            # 跳过 Triage，使用旧版单 Agent 模式
#   ./run_eval.sh --quick                # 快速抽样（每类 3 个）
#
# 环境变量（可选覆盖）:
#   OPENAI_API_KEY          — 覆盖 .env 中的 API Key
#   LLM_MODEL               — 覆盖 RAG Agent 模型（默认 gpt-4o）
#   EVAL_CONCURRENCY        — 并发数（默认 3）
#   EVAL_JUDGE_MODELS       — Judge 模型列表（默认 gpt-4o）

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RAG_API_DIR="$PROJECT_ROOT/apps/rag-api"

# ── 加载 API Key ──────────────────────────────────────────────────────────
# 优先级: 环境变量 > 项目根目录 .env > apps/rag-api/.env
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        OPENAI_API_KEY=$(grep -m1 '^OPENAI_API_KEY=' "$PROJECT_ROOT/.env" | cut -d= -f2)
    elif [[ -f "$SCRIPT_DIR/.env" ]]; then
        OPENAI_API_KEY=$(grep -m1 '^OPENAI_API_KEY=' "$SCRIPT_DIR/.env" | cut -d= -f2)
    elif [[ -f "$RAG_API_DIR/.env" ]]; then
        OPENAI_API_KEY=$(grep -m1 '^OPENAI_API_KEY=' "$RAG_API_DIR/.env" | cut -d= -f2)
    fi
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "❌ OPENAI_API_KEY 未设置。请配置 .env 文件或通过环境变量传入。"
    exit 1
fi

export OPENAI_API_KEY

# ── 快速模式：每类抽 3 个用例 ─────────────────────────────────────────────
EXTRA_ARGS=()
QUICK_MODE=false

for arg in "$@"; do
    if [[ "$arg" == "--quick" ]]; then
        QUICK_MODE=true
    else
        EXTRA_ARGS+=("$arg")
    fi
done

if $QUICK_MODE; then
    SAMPLE_IDS=$(cd "$SCRIPT_DIR" && python3 -c "
import json, random
random.seed(42)
with open('test_cases.json') as f:
    data = json.load(f)
by_type = {}
for tc in data['test_cases']:
    by_type.setdefault(tc['question_type'], []).append(tc['id'])
ids = []
for qt, id_list in by_type.items():
    ids.extend(random.sample(id_list, min(3, len(id_list))))
print(' '.join(str(i) for i in sorted(ids)))
")
    EXTRA_ARGS+=("--ids" $SAMPLE_IDS)
    echo "⚡ 快速模式：抽样 $(echo $SAMPLE_IDS | wc -w | tr -d ' ') 个用例"
fi

# ── 可选覆盖 ──────────────────────────────────────────────────────────────
if [[ -n "${EVAL_CONCURRENCY:-}" ]]; then
    EXTRA_ARGS+=("--concurrency" "$EVAL_CONCURRENCY")
fi

if [[ -n "${EVAL_JUDGE_MODELS:-}" ]]; then
    EXTRA_ARGS+=("--judge-models" $EVAL_JUDGE_MODELS)
fi

# ── 启动评测 ──────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  FF Robot RAG 评测"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  模型: ${LLM_MODEL:-gpt-4o}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

cd "$SCRIPT_DIR"
exec python -u run_eval.py "${EXTRA_ARGS[@]}"
