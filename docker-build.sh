#!/usr/bin/env bash
#
# 构建 Docker 镜像到本地
#
# Usage:
#   ./docker-build.sh              # 仅构建镜像
#   ./docker-build.sh --run        # 构建镜像并重启本地服务
#   ./docker-build.sh --no-cache   # 不使用缓存，全新构建
#
# 构建完成后：
#   docker compose up -d           # 本地启动测试
#   open http://localhost           # 浏览器验证
#   docker compose down             # 停止
#
# 确认没问题后：
#   ./aws-deploy.sh                # 推送到 AWS 并部署
#
set -euo pipefail

IMAGE_NAME="eai-robot-app"
CHATKIT_DOMAIN_KEY="domain_pk_69b16130965481908afd31f4830f42c00e39b325f6d7c5d1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

EXTRA_ARGS=""
RUN_AFTER=false
for arg in "$@"; do
    case "$arg" in
        --no-cache) EXTRA_ARGS="$EXTRA_ARGS --no-cache" ;;
        --run)      RUN_AFTER=true ;;
    esac
done

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Docker 镜像构建"
echo "═══════════════════════════════════════════════════════"
echo ""

echo "🔨 构建中（目标平台: linux/amd64）..."
docker buildx build $EXTRA_ARGS --platform linux/amd64 \
    --build-arg VITE_CHATKIT_DOMAIN_KEY="$CHATKIT_DOMAIN_KEY" \
    -t "$IMAGE_NAME" -f Dockerfile .

IMAGE_SIZE=$(docker images "$IMAGE_NAME:latest" --format "{{.Size}}" 2>/dev/null || echo "unknown")
echo ""
echo "✅ 构建完成！ 镜像: $IMAGE_NAME ($IMAGE_SIZE)"

if [ "$RUN_AFTER" = true ]; then
    echo ""
    echo "🚀 重启本地服务..."
    docker compose up -d
    echo ""
    echo "  访问: http://localhost"
    echo "  日志: docker compose logs -f"
else
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  下一步："
    echo ""
    echo "  本地运行:    ./docker-build.sh --run"
    echo "               或 docker compose up -d"
    echo "  发布到 AWS:  ./aws-deploy.sh"
    echo "═══════════════════════════════════════════════════════"
fi
echo ""
