#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "🔧 虚拟环境不存在，正在创建 ..."
    python3 -m venv "$VENV_DIR"
    echo "✅ 虚拟环境创建完成"
fi

source "$VENV_DIR/bin/activate"

if [ ! -f "$VENV_DIR/.deps_installed" ]; then
    echo "📦 首次运行，正在安装依赖 ..."
    pip install -r requirements.txt
    touch "$VENV_DIR/.deps_installed"
    echo "✅ 依赖安装完成"
fi

echo "🚀 启动 RAG Server ..."
exec uvicorn app.main:app --reload --port 8000
