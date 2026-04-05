#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${CLIENT_PORT:-5173}"
RAG_PORT="${RAG_PORT:-8000}"
PKG_FILE="$SCRIPT_DIR/package-lock.json"

# ── Node.js check ─────────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
    echo "❌ 未找到 Node.js，请先安装 (https://nodejs.org/)"
    exit 1
fi

echo "   Node $(node -v) | npm $(npm -v 2>/dev/null || echo '?')"

# ── Dependencies (reinstall when package.json changes) ────────────────
HASH_FILE="$SCRIPT_DIR/node_modules/.pkg_hash"
if [ ! -f "$PKG_FILE" ]; then
    CURRENT_HASH="no-lockfile"
else
    CURRENT_HASH=$(md5sum "$PKG_FILE" 2>/dev/null | awk '{print $1}' || md5 -q "$PKG_FILE" 2>/dev/null || echo "unknown")
fi

if [ ! -d "node_modules" ] || [ ! -f "$HASH_FILE" ] || [ "$(cat "$HASH_FILE")" != "$CURRENT_HASH" ]; then
    echo "📦 安装/更新依赖 ..."
    npm install --silent
    echo "$CURRENT_HASH" > "$HASH_FILE"
    echo "✅ 依赖安装完成"
fi

# ── Check chat SDK exists ─────────────────────────────────────────────
SDK_FILE="$SCRIPT_DIR/public/dist-embed/ffrobot-chat-sdk.js"
if [ ! -f "$SDK_FILE" ]; then
    echo "⚠️  未找到 apps/web/public/dist-embed/ffrobot-chat-sdk.js，Chat 面板不可用"
    echo "   请先运行: ./packages/chat-sdk/build.sh debug"
fi

# ── Launch ────────────────────────────────────────────────────────────
export VITE_CHAT_SERVICE_ORIGIN="${VITE_CHAT_SERVICE_ORIGIN:-http://127.0.0.1:8000}"

echo ""
echo "🚀 启动前端开发服务器 (port $PORT)"
echo "   前端地址:    https://localhost:$PORT"
echo "   Chat 服务域名: $VITE_CHAT_SERVICE_ORIGIN"
echo "   搜索 API:    /api/search → http://localhost:$RAG_PORT/api/search (Vite proxy)"
echo ""
exec npm run dev -w web -- --host --port "$PORT"
