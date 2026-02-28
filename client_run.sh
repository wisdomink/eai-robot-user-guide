#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${CLIENT_PORT:-5173}"
RAG_PORT="${RAG_PORT:-8000}"
PKG_FILE="$SCRIPT_DIR/package.json"

# ── Node.js check ─────────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
    echo "❌ 未找到 Node.js，请先安装 (https://nodejs.org/)"
    exit 1
fi

echo "   Node $(node -v) | npm $(npm -v 2>/dev/null || echo '?')"

# ── Dependencies (reinstall when package.json changes) ────────────────
HASH_FILE="$SCRIPT_DIR/node_modules/.pkg_hash"
CURRENT_HASH=$(md5sum "$PKG_FILE" 2>/dev/null || md5 -q "$PKG_FILE" 2>/dev/null || echo "unknown")

if [ ! -d "node_modules" ] || [ ! -f "$HASH_FILE" ] || [ "$(cat "$HASH_FILE")" != "$CURRENT_HASH" ]; then
    echo "📦 安装/更新依赖 ..."
    npm install --silent
    echo "$CURRENT_HASH" > "$HASH_FILE"
    echo "✅ 依赖安装完成"
fi

# ── Launch ────────────────────────────────────────────────────────────
export VITE_CHATKIT_API_URL="${VITE_CHATKIT_API_URL:-http://localhost:$RAG_PORT/chatkit}"

echo ""
echo "🚀 启动前端开发服务器 (port $PORT)"
echo "   ChatKit API: $VITE_CHATKIT_API_URL"
echo ""
exec npx vite --host --port "$PORT"
