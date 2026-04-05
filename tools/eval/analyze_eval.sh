#!/usr/bin/env bash
#
# FF Robot RAG 评测结果多角色分析
#
# 用法：
#   ./analyze_eval.sh                                        # 分析最新报告
#   ./analyze_eval.sh --report reports/report_xxx.json       # 指定报告
#   ./analyze_eval.sh --compare reports/report_old.json      # 与旧版对比
#   ./analyze_eval.sh --model gpt-4.1                        # 指定分析模型

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RAG_API_DIR="$PROJECT_ROOT/apps/rag-api"

# ── 加载 API Key ──────────────────────────────────────────────────────────
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

cd "$SCRIPT_DIR"
exec python -u analyze_eval.py "$@"
