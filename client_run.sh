#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v node &>/dev/null; then
    echo "❌ 未找到 Node.js，请先安装 Node.js (https://nodejs.org/)"
    exit 1
fi

if [ ! -d "node_modules" ]; then
    echo "📦 node_modules 不存在，正在安装依赖 ..."
    npm install
    echo "✅ 依赖安装完成"
fi

echo "🚀 启动前端开发服务器 ..."
exec npx vite --host
