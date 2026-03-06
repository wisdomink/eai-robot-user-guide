#!/usr/bin/env bash
#
# 测试环境部署脚本 (Ubuntu)
#
# 自动安装依赖、配置环境、启动前端 + RAG 后端两个服务。
# 前端使用 Vite 开发服务器（含热更新），后端使用 Uvicorn（含 auto-reload）。
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh           # 启动所有服务
#   ./deploy.sh stop      # 停止所有服务
#   ./deploy.sh status    # 查看服务状态
#   ./deploy.sh restart   # 重启所有服务
#
set -euo pipefail

# 防止 source 方式运行（`. deploy.sh` 会导致退出当前 shell）
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
    echo "❌ 请不要用 source 运行此脚本，请使用: ./deploy.sh"
    return 1 2>/dev/null || true
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

CLIENT_PORT="${CLIENT_PORT:-5173}"
RAG_PORT="${RAG_PORT:-8000}"

PID_DIR="$SCRIPT_DIR/.pids"
FRONTEND_PID="$PID_DIR/frontend.pid"
RAG_PID="$PID_DIR/rag.pid"
LOG_DIR="$SCRIPT_DIR/.logs"
FRONTEND_LOG="$LOG_DIR/frontend.log"
RAG_LOG="$LOG_DIR/rag.log"

mkdir -p "$PID_DIR" "$LOG_DIR"

# ── Helpers ───────────────────────────────────────────────────────────

is_running() {
    [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null
}

stop_service() {
    local pid_file="$1" name="$2"
    if is_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        # 先杀整个进程组（setsid 创建的会话），再杀主进程兜底
        kill -- -"$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
        echo "   ⏹  $name (PID $pid) 已停止"
    else
        echo "   ○  $name 未在运行"
    fi
    rm -f "$pid_file"
}

kill_port() {
    local port="$1" name="$2"
    local pids
    pids=$(lsof -ti :"$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -9 2>/dev/null || true
        echo "   ⏹  清理端口 $port 上的残留进程 ($name)"
        sleep 1
    fi
}

show_status() {
    local pid_file="$1" name="$2" log_file="$3"
    if is_running "$pid_file"; then
        echo "   ● $name — 运行中 (PID $(cat "$pid_file"))"
    else
        echo "   ○ $name — 未运行"
    fi
    if [ -f "$log_file" ]; then
        echo "     日志: $log_file"
    fi
}

# ── Commands: stop / status ───────────────────────────────────────────

ACTION="${1:-start}"

if [ "$ACTION" = "stop" ]; then
    echo ""
    echo "⏹  停止服务..."
    stop_service "$FRONTEND_PID" "前端 (Vite)"
    stop_service "$RAG_PID" "RAG Server"
    kill_port "$CLIENT_PORT" "前端"
    kill_port "$RAG_PORT" "RAG Server"
    echo ""
    exit 0
fi

if [ "$ACTION" = "status" ]; then
    echo ""
    echo "═══ 服务状态 ═══"
    show_status "$FRONTEND_PID" "前端 (Vite :$CLIENT_PORT)" "$FRONTEND_LOG"
    show_status "$RAG_PID" "RAG Server (:$RAG_PORT)" "$RAG_LOG"
    echo ""
    exit 0
fi

if [ "$ACTION" = "restart" ]; then
    "$0" stop
    sleep 1
    exec "$0" start
fi

# ── Start flow ────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  EAI Robot User Guide — 测试环境部署"
echo "═══════════════════════════════════════════════════════"
echo ""

# ── 1. Check Node.js ──────────────────────────────────────────────────

if ! command -v node &>/dev/null; then
    echo "📦 安装 Node.js..."
    if command -v apt-get &>/dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
        sudo apt-get install -y nodejs
    else
        echo "❌ 未找到 Node.js，请手动安装: https://nodejs.org/"
        exit 1
    fi
fi
echo "✅ Node.js $(node -v)"

# ── 2. Check Python 3 ────────────────────────────────────────────────

if ! command -v python3 &>/dev/null; then
    echo "📦 安装 Python 3..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y python3 python3-venv python3-pip
    else
        echo "❌ 未找到 Python 3，请手动安装"
        exit 1
    fi
fi
echo "✅ $(python3 --version)"

# ── 3. Check .env file ───────────────────────────────────────────────

RAG_ENV="$SCRIPT_DIR/rag_server/.env"

if [ ! -f "$RAG_ENV" ]; then
    if [ -f "$SCRIPT_DIR/rag_server/.env.example" ]; then
        cp "$SCRIPT_DIR/rag_server/.env.example" "$RAG_ENV"
    fi
    echo "⚠️  请编辑 rag_server/.env 填入 OPENAI_API_KEY 后重新运行"
    exit 1
fi

echo "✅ .env 配置就绪 ($RAG_ENV)"

# ── 4. Install frontend dependencies ─────────────────────────────────

HASH_FILE="$SCRIPT_DIR/node_modules/.pkg_hash"
CURRENT_HASH=$(md5sum "$SCRIPT_DIR/package.json" 2>/dev/null | awk '{print $1}' || echo "unknown")

if [ ! -d "node_modules" ] || [ ! -f "$HASH_FILE" ] || [ "$(cat "$HASH_FILE")" != "$CURRENT_HASH" ]; then
    echo "📦 安装前端依赖..."
    npm install --silent
    echo "$CURRENT_HASH" > "$HASH_FILE"
fi
echo "✅ 前端依赖就绪"

# ── 5. Setup RAG server venv ──────────────────────────────────────────

RAG_VENV="$SCRIPT_DIR/rag_server/venv"

if [ ! -d "$RAG_VENV" ]; then
    echo "📦 创建 Python 虚拟环境 (venv)..."
    python3 -m venv "$RAG_VENV"
fi

RAG_HASH_FILE="$RAG_VENV/.deps_hash"
RAG_HASH=$(md5sum "$SCRIPT_DIR/rag_server/requirements.txt" 2>/dev/null | awk '{print $1}' || echo "unknown")

if [ ! -f "$RAG_HASH_FILE" ] || [ "$(cat "$RAG_HASH_FILE")" != "$RAG_HASH" ]; then
    echo "📦 安装 RAG Server 依赖..."
    "$RAG_VENV/bin/pip" install -q -r "$SCRIPT_DIR/rag_server/requirements.txt"
    echo "$RAG_HASH" > "$RAG_HASH_FILE"
fi
echo "✅ RAG Server 依赖就绪"
echo ""

# ── 6. Stop existing services if running ──────────────────────────────

stop_service "$RAG_PID" "旧 RAG Server"
stop_service "$FRONTEND_PID" "旧 Vite 前端"
kill_port "$RAG_PORT" "RAG Server"
kill_port "$CLIENT_PORT" "前端"

# ── 7. Start RAG server ──────────────────────────────────────────────

echo "🚀 启动 RAG Server (port $RAG_PORT)..."
cd "$SCRIPT_DIR/rag_server"
setsid nohup "$RAG_VENV/bin/uvicorn" app.main:app --host 0.0.0.0 --port "$RAG_PORT" \
    > "$RAG_LOG" 2>&1 < /dev/null &
echo $! > "$RAG_PID"
cd "$SCRIPT_DIR"

# ── 8. Start Vite dev server ─────────────────────────────────────────

echo "🚀 启动 Vite 前端 (port $CLIENT_PORT)..."
setsid nohup npx vite --host --port "$CLIENT_PORT" \
    > "$FRONTEND_LOG" 2>&1 < /dev/null &
echo $! > "$FRONTEND_PID"

# Wait for services to start
sleep 3

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ 测试环境部署完成！"
echo ""
echo "  前端:       https://0.0.0.0:$CLIENT_PORT"
echo "  RAG Server: http://0.0.0.0:$RAG_PORT"
echo ""
echo "  查看日志:"
echo "    tail -f $FRONTEND_LOG"
echo "    tail -f $RAG_LOG"
echo ""
echo "  管理:"
echo "    ./deploy.sh status   — 查看状态"
echo "    ./deploy.sh stop     — 停止服务"
echo "    ./deploy.sh restart  — 重启服务"
echo "═══════════════════════════════════════════════════════"
echo ""
