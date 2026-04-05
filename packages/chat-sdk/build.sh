#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  packages/chat-sdk/build.sh
#
#  Build the FFRobotChat JS SDK (IIFE bundle).
#  Output:
#    <repo-root>/dist-embed/ffrobot-chat-sdk.js
#    <repo-root>/apps/web/public/dist-embed/ffrobot-chat-sdk.js
#
#  Usage:
#    ./packages/chat-sdk/build.sh debug     # API -> http://127.0.0.1:8000
#    ./packages/chat-sdk/build.sh release   # API -> https://robotics-instruction-manual.ff.com
#    ./packages/chat-sdk/build.sh           # same as debug
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PKG_DIR="$SCRIPT_DIR"
OUT_DIR="$REPO_ROOT/dist-embed"
SDK_FILE="$OUT_DIR/ffrobot-chat-sdk.js"
WEB_PUBLIC_DIR="$REPO_ROOT/apps/web/public"
WEB_PUBLIC_EXTERNAL_DIR="$WEB_PUBLIC_DIR/dist-embed"

DEBUG_ORIGIN="http://127.0.0.1:8000"
RELEASE_ORIGIN="https://robotics-instruction-manual.ff.com"
RELEASE_CHATKIT_DOMAIN_KEY="domain_pk_69d52b6b7cb08193b207b84802aa895d08baab6db3c053fa"

# ── Colors ────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { printf "${CYAN}[chat-sdk]${NC} %s\n" "$*"; }
ok()   { printf "${GREEN}[chat-sdk]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[chat-sdk]${NC} %s\n" "$*"; }
err()  { printf "${RED}[chat-sdk]${NC} %s\n" "$*" >&2; }

# ── Parse mode ────────────────────────────────────────────────
MODE="${1:-debug}"

case "$MODE" in
  debug)
    export VITE_CHAT_SERVICE_ORIGIN="$DEBUG_ORIGIN"
    ;;
  release)
    export VITE_CHAT_SERVICE_ORIGIN="$RELEASE_ORIGIN"
    export VITE_CHATKIT_DOMAIN_KEY="$RELEASE_CHATKIT_DOMAIN_KEY"
    ;;
  *)
    err "Unknown mode: $MODE"
    echo ""
    echo "Usage: $0 [debug|release]"
    echo ""
    echo "  debug   — API origin: $DEBUG_ORIGIN (default)"
    echo "  release — API origin: $RELEASE_ORIGIN"
    exit 1
    ;;
esac

# ── Pre-flight checks ────────────────────────────────────────
if ! command -v node &>/dev/null; then
  err "Node.js is not installed. Please install Node.js >= 18."
  exit 1
fi

NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
  err "Node.js >= 18 required (current: $(node -v))."
  exit 1
fi

if [ ! -d "$REPO_ROOT/node_modules" ]; then
  warn "node_modules not found — running npm install ..."
  (cd "$REPO_ROOT" && npm install)
fi

# ── Build info ────────────────────────────────────────────────
log "Building FFRobotChat JS SDK ..."
log "  Mode        : $MODE"
log "  API origin  : $VITE_CHAT_SERVICE_ORIGIN"
log "  Package dir : $PKG_DIR"
log "  Output dir  : $OUT_DIR"

if [ -n "${VITE_CHATKIT_DOMAIN_KEY:-}" ]; then
  log "  Domain key  : $VITE_CHATKIT_DOMAIN_KEY"
fi

# ── Build ─────────────────────────────────────────────────────
(cd "$PKG_DIR" && npx vite build)

# ── Verify output ─────────────────────────────────────────────
if [ ! -f "$SDK_FILE" ]; then
  err "Build failed — expected output not found: $SDK_FILE"
  exit 1
fi

FILE_SIZE=$(wc -c < "$SDK_FILE" | tr -d ' ')
FILE_SIZE_KB=$(( FILE_SIZE / 1024 ))
WEB_PUBLIC_EXTERNAL_DEST="$WEB_PUBLIC_EXTERNAL_DIR/ffrobot-chat-sdk.js"

# ── Sync to apps/web/public/ (for Vite dev server + Docker build) ────
mkdir -p "$WEB_PUBLIC_EXTERNAL_DIR"
cp "$SDK_FILE" "$WEB_PUBLIC_EXTERNAL_DEST"

ok "Build succeeded! [$MODE]"
ok "  dist-embed : $SDK_FILE"
ok "  web/public : $WEB_PUBLIC_EXTERNAL_DEST"
ok "  Size       : ${FILE_SIZE_KB} KB (${FILE_SIZE} bytes)"
