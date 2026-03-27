#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${RAG_PORT:-8000}"
VENV_DIR="$SCRIPT_DIR/venv"
REQ_FILE="$SCRIPT_DIR/requirements.txt"
ENV_FILE="$SCRIPT_DIR/.env"

# ── Python check ──────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "❌ 未找到 Python 3，请先安装 (https://www.python.org/downloads/)"
    exit 1
fi

# ── .env check ────────────────────────────────────────────────────────
if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        echo "⚠️  未找到 .env，已从 .env.example 创建模板"
        cp "$SCRIPT_DIR/.env.example" "$ENV_FILE"
        echo "   请编辑 $ENV_FILE 填入你的 API Key"
        exit 1
    else
        echo "⚠️  未找到 .env 文件，请参考 .env.example 创建"
        exit 1
    fi
fi

source "$ENV_FILE" 2>/dev/null || true

if [ -z "${OPENAI_API_KEY:-}" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-key-here" ]; then
    echo "❌ 请在 $ENV_FILE 中设置有效的 OPENAI_API_KEY"
    exit 1
fi

VS_COUNT=0
for vs_var in OPENAI_VECTOR_STORE_MASTER_ULTRA_ID OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID \
              OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID OPENAI_VECTOR_STORE_AEGIS_EDU_ID \
              OPENAI_VECTOR_STORE_FF91_ID OPENAI_VECTOR_STORE_ROBOT_ALL_ID; do
    val="${!vs_var:-}"
    if [ -n "$val" ] && [ "$val" != "vs_xxx" ]; then
        VS_COUNT=$((VS_COUNT + 1))
    fi
done

if [ "$VS_COUNT" -eq 0 ]; then
    echo "⚠️  未在 $ENV_FILE 中检测到任何有效的 Vector Store ID"
    echo "   如尚未创建 Vector Store，请先运行: python create_vector_store.py"
    exit 1
fi

# ── Virtual environment ───────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "🔧 虚拟环境不存在，正在创建 ..."
    python3 -m venv "$VENV_DIR"
    echo "✅ 虚拟环境创建完成"
fi

source "$VENV_DIR/bin/activate"

# ── Dependencies (reinstall when requirements.txt changes) ────────────
DEPS_HASH_FILE="$VENV_DIR/.deps_hash"
CURRENT_HASH=$(md5sum "$REQ_FILE" 2>/dev/null || md5 -q "$REQ_FILE" 2>/dev/null || echo "unknown")

if [ ! -f "$DEPS_HASH_FILE" ] || [ "$(cat "$DEPS_HASH_FILE")" != "$CURRENT_HASH" ]; then
    echo "📦 安装/更新依赖 ..."
    pip install -q -r "$REQ_FILE"
    echo "$CURRENT_HASH" > "$DEPS_HASH_FILE"
    echo "✅ 依赖安装完成"
fi

# ── Launch ────────────────────────────────────────────────────────────
echo ""
echo "🚀 启动 ChatKit RAG Server (port $PORT)"
echo "   ChatKit 端点:    http://localhost:$PORT/api/chatkit"
echo "   语义搜索端点:    http://localhost:$PORT/api/search"
echo "   健康检查:        http://localhost:$PORT/health"
echo "   Model:          ${LLM_MODEL:-gpt-5}"
echo "   Vector Stores:  $VS_COUNT configured"
echo ""
exec uvicorn app.main:app --reload --host 0.0.0.0 --port "$PORT"
