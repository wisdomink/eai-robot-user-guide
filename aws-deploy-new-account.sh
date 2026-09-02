#!/usr/bin/env bash
#
# 构建 Docker 镜像并部署到新的 AWS 账号 ECS
#
# Usage:
#   ./aws-deploy-new-account.sh --build
#   AWS_PROFILE=eai-robot-new ./aws-deploy-new-account.sh --build
#   ./aws-deploy-new-account.sh --profile eai-robot-new --build
#   ./aws-deploy-new-account.sh --profile eai-robot-new setup-ssl <域名>
#   ./aws-deploy-new-account.sh --profile eai-robot-new status
#   ./aws-deploy-new-account.sh --profile eai-robot-new logs
#   ./aws-deploy-new-account.sh --profile eai-robot-new destroy
#
set -euo pipefail

# ══════════════════════════════════════════════════════════
#  新账号部署配置
# ══════════════════════════════════════════════════════════

# 新 AWS 账号凭证。请在本地填入新账号的 Access Key，不要填旧账号凭证。
# 留空时，脚本会使用 AWS_PROFILE、环境变量或默认 AWS CLI 凭证。
HARDCODED_AWS_ACCESS_KEY_ID="xxx"
HARDCODED_AWS_SECRET_ACCESS_KEY="xxx"
HARDCODED_AWS_SESSION_TOKEN=""

AWS_REGION="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
export AWS_DEFAULT_REGION="$AWS_REGION"

if [ -n "$HARDCODED_AWS_ACCESS_KEY_ID" ] || [ -n "$HARDCODED_AWS_SECRET_ACCESS_KEY" ]; then
    if [ -z "$HARDCODED_AWS_ACCESS_KEY_ID" ] || [ -z "$HARDCODED_AWS_SECRET_ACCESS_KEY" ]; then
        echo "❌ HARDCODED_AWS_ACCESS_KEY_ID 和 HARDCODED_AWS_SECRET_ACCESS_KEY 必须同时填写。"
        exit 1
    fi
    export AWS_ACCESS_KEY_ID="$HARDCODED_AWS_ACCESS_KEY_ID"
    export AWS_SECRET_ACCESS_KEY="$HARDCODED_AWS_SECRET_ACCESS_KEY"
    if [ -n "$HARDCODED_AWS_SESSION_TOKEN" ]; then
        export AWS_SESSION_TOKEN="$HARDCODED_AWS_SESSION_TOKEN"
    else
        unset AWS_SESSION_TOKEN || true
    fi
    unset AWS_PROFILE || true
fi

# 新账号安全护栏：所有 AWS 操作必须在此账号中执行。
# 不允许从环境变量或命令行覆盖，避免误部署到旧账号。
EXPECTED_AWS_ACCOUNT_ID="018079438010"

APP_NAME="eai-robot"
IMAGE_NAME="eai-robot-app"
ECR_REPO_NAME="eai-robot-app"
LEADS_DDB_TABLE="${APP_NAME}-leads"
RECOMMENDATIONS_DDB_TABLE="${APP_NAME}-recommendations"
HOMEPAGE_PROMPTS_DDB_TABLE="${APP_NAME}-homepage-prompts"
TASK_ROLE_NAME="${APP_NAME}-task-role"
CONTAINER_PORT=80
CPU=512        # 0.5 vCPU
MEMORY=1024    # 1 GB

# 正式切流后默认使用生产域名；如需临时验证，可在运行前覆盖为测试域名。
# 例如：PRODUCTION_CHAT_SERVICE_ORIGIN=https://robotics-instruction-manual-new.ff.com ./aws-deploy-new-account.sh --build
PRODUCTION_CHAT_SERVICE_ORIGIN="${PRODUCTION_CHAT_SERVICE_ORIGIN:-https://robotics-instruction-manual.ff.com}"
CHATKIT_DOMAIN_KEY="domain_pk_69d52b6b7cb08193b207b84802aa895d08baab6db3c053fa"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/apps/rag-api/.env"
DEPLOY_CONFIG="${DEPLOY_CONFIG:-$SCRIPT_DIR/.deploy-config-new-account}"

# 可选网络覆盖。若新账号没有 default VPC，可在运行时指定：
# DEPLOY_VPC_ID=vpc-xxx DEPLOY_SUBNET_IDS=subnet-a,subnet-b ./aws-deploy-new-account.sh --profile eai-robot-new --build
DEPLOY_VPC_ID="${DEPLOY_VPC_ID:-}"
DEPLOY_SUBNET_IDS="${DEPLOY_SUBNET_IDS:-}"

# ══════════════════════════════════════════════════════════
#  工具函数
# ══════════════════════════════════════════════════════════

print_context() {
    if [ -n "$HARDCODED_AWS_ACCESS_KEY_ID" ]; then
        echo "  AWS Auth:     hardcoded access key (${HARDCODED_AWS_ACCESS_KEY_ID:0:4}...)"
    else
        echo "  AWS Auth:     profile/env (${AWS_PROFILE:-default})"
    fi
    echo "  AWS Account:  ${AWS_ACCOUNT_ID:-unknown}"
    echo "  Region:       $AWS_REGION"
    echo "  Config file:  $DEPLOY_CONFIG"
}

check_prerequisites() {
    if ! command -v aws &>/dev/null; then
        echo "❌ AWS CLI 未安装。请运行: brew install awscli"
        exit 1
    fi
    if ! aws sts get-caller-identity &>/dev/null; then
        echo "❌ AWS 凭证无效。请确认脚本顶部硬编码凭证、AWS_PROFILE 或默认 AWS CLI 凭证已配置。"
        echo "   示例: aws configure --profile eai-robot-new"
        exit 1
    fi
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    if [ -n "$EXPECTED_AWS_ACCOUNT_ID" ] && [ "$AWS_ACCOUNT_ID" != "$EXPECTED_AWS_ACCOUNT_ID" ]; then
        echo "❌ 当前 AWS 账号不匹配，已停止。"
        echo "   当前账号: $AWS_ACCOUNT_ID"
        echo "   预期账号: $EXPECTED_AWS_ACCOUNT_ID"
        exit 1
    fi
    if ! command -v docker &>/dev/null || ! docker info &>/dev/null 2>&1; then
        echo "❌ Docker 未运行。请启动 Docker Desktop"
        exit 1
    fi
}

load_config() {
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    if [ -n "$EXPECTED_AWS_ACCOUNT_ID" ] && [ "$AWS_ACCOUNT_ID" != "$EXPECTED_AWS_ACCOUNT_ID" ]; then
        echo "❌ 当前 AWS 账号不匹配，已停止。"
        echo "   当前账号: $AWS_ACCOUNT_ID"
        echo "   预期账号: $EXPECTED_AWS_ACCOUNT_ID"
        exit 1
    fi

    if [ -f "$DEPLOY_CONFIG" ]; then
        source "$DEPLOY_CONFIG"
        if [ -n "${CONFIG_AWS_ACCOUNT_ID:-}" ] && [ "$CONFIG_AWS_ACCOUNT_ID" != "$AWS_ACCOUNT_ID" ]; then
            echo "❌ 部署配置文件账号与当前 AWS 账号不一致，已停止。"
            echo "   配置文件: $DEPLOY_CONFIG"
            echo "   配置账号: $CONFIG_AWS_ACCOUNT_ID"
            echo "   当前账号: $AWS_ACCOUNT_ID"
            echo "   如需全新部署，请换一个 DEPLOY_CONFIG，或确认后手动处理该配置文件。"
            exit 1
        fi
    fi

    export AWS_DEFAULT_REGION="$AWS_REGION"
    ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    ECR_IMAGE="$ECR_REGISTRY/$ECR_REPO_NAME:latest"
}

save_config() {
    local current_image_id
    current_image_id=$(docker images "$IMAGE_NAME:latest" --format "{{.ID}}" 2>/dev/null || echo "")
    cat > "$DEPLOY_CONFIG" << EOF
# Auto-generated — do not edit
CONFIG_AWS_ACCOUNT_ID="$AWS_ACCOUNT_ID"
AWS_REGION="$AWS_REGION"
ECS_CLUSTER_NAME="$ECS_CLUSTER_NAME"
ECS_SERVICE_NAME="$ECS_SERVICE_NAME"
TASK_FAMILY="$TASK_FAMILY"
TASK_ROLE_ARN="${TASK_ROLE_ARN:-}"
ALB_ARN="$ALB_ARN"
TG_ARN="$TG_ARN"
SG_ID="$SG_ID"
SUBNET_IDS="$SUBNET_IDS"
VPC_ID="$VPC_ID"
LAST_PUSHED_IMAGE_ID="$current_image_id"
CERT_ARN="${CERT_ARN:-}"
CUSTOM_DOMAIN="${CUSTOM_DOMAIN:-}"
EOF
}

parse_env_file() {
    local env_json="["
    local first=true
    while IFS= read -r line || [ -n "$line" ]; do
        line=$(echo "$line" | sed 's/#.*//' | xargs)
        [ -z "$line" ] && continue
        local key="${line%%=*}"
        local value="${line#*=}"
        [ -z "$key" ] && continue
        if [ "$first" = true ]; then first=false; else env_json+=","; fi
        env_json+="{\"name\":\"$key\",\"value\":\"$value\"}"
    done < "$ENV_FILE"
    env_json+="]"
    echo "$env_json"
}

build_task_env_json() {
    local base_json="$1"
    BASE_JSON="$base_json" \
    AWS_REGION="$AWS_REGION" \
    LEADS_DDB_TABLE="$LEADS_DDB_TABLE" \
    RECOMMENDATIONS_DDB_TABLE="$RECOMMENDATIONS_DDB_TABLE" \
    HOMEPAGE_PROMPTS_DDB_TABLE="$HOMEPAGE_PROMPTS_DDB_TABLE" \
    python3 - <<'PY'
import json
import os

data = json.loads(os.environ["BASE_JSON"])
extra = {
    "AWS_DEFAULT_REGION": os.environ["AWS_REGION"],
    "LEADS_BACKEND": "dynamodb",
    "LEADS_DDB_TABLE": os.environ["LEADS_DDB_TABLE"],
    "RECOMMENDATIONS_BACKEND": "dynamodb",
    "RECOMMENDATIONS_DDB_TABLE": os.environ["RECOMMENDATIONS_DDB_TABLE"],
    "HOMEPAGE_PROMPTS_BACKEND": "dynamodb",
    "HOMEPAGE_PROMPTS_DDB_TABLE": os.environ["HOMEPAGE_PROMPTS_DDB_TABLE"],
}

index_by_name = {
    item.get("name"): idx
    for idx, item in enumerate(data)
    if isinstance(item, dict) and item.get("name")
}

for key, value in extra.items():
    item = {"name": key, "value": value}
    if key in index_by_name:
        data[index_by_name[key]] = item
    else:
        data.append(item)

print(json.dumps(data))
PY
}

ensure_dynamodb_tables() {
    echo ""
    echo "══ 配置 DynamoDB ══"

    aws dynamodb describe-table \
        --table-name "$LEADS_DDB_TABLE" \
        --region "$AWS_REGION" >/dev/null 2>&1 || {
        echo "  📦 创建表: $LEADS_DDB_TABLE"
        aws dynamodb create-table \
            --table-name "$LEADS_DDB_TABLE" \
            --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
            --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
            --billing-mode PAY_PER_REQUEST \
            --region "$AWS_REGION" >/dev/null
        aws dynamodb wait table-exists --table-name "$LEADS_DDB_TABLE" --region "$AWS_REGION"
    }

    aws dynamodb describe-table \
        --table-name "$RECOMMENDATIONS_DDB_TABLE" \
        --region "$AWS_REGION" >/dev/null 2>&1 || {
        echo "  📦 创建表: $RECOMMENDATIONS_DDB_TABLE"
        aws dynamodb create-table \
            --table-name "$RECOMMENDATIONS_DDB_TABLE" \
            --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
            --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
            --billing-mode PAY_PER_REQUEST \
            --region "$AWS_REGION" >/dev/null
        aws dynamodb wait table-exists --table-name "$RECOMMENDATIONS_DDB_TABLE" --region "$AWS_REGION"
    }

    aws dynamodb describe-table \
        --table-name "$HOMEPAGE_PROMPTS_DDB_TABLE" \
        --region "$AWS_REGION" >/dev/null 2>&1 || {
        echo "  📦 创建表: $HOMEPAGE_PROMPTS_DDB_TABLE"
        aws dynamodb create-table \
            --table-name "$HOMEPAGE_PROMPTS_DDB_TABLE" \
            --attribute-definitions AttributeName=pk,AttributeType=S AttributeName=sk,AttributeType=S \
            --key-schema AttributeName=pk,KeyType=HASH AttributeName=sk,KeyType=RANGE \
            --billing-mode PAY_PER_REQUEST \
            --region "$AWS_REGION" >/dev/null
        aws dynamodb wait table-exists --table-name "$HOMEPAGE_PROMPTS_DDB_TABLE" --region "$AWS_REGION"
    }

    echo "  ✅ DynamoDB 表已就绪"
}

ensure_task_role() {
    local assume_policy dynamodb_policy
    assume_policy='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

    TASK_ROLE_ARN=$(aws iam get-role --role-name "$TASK_ROLE_NAME" --query "Role.Arn" --output text 2>/dev/null || echo "")
    if [ -z "$TASK_ROLE_ARN" ] || [ "$TASK_ROLE_ARN" = "None" ]; then
        echo "  📦 创建 ECS 应用角色..."
        aws iam create-role \
            --role-name "$TASK_ROLE_NAME" \
            --assume-role-policy-document "$assume_policy" >/dev/null
        TASK_ROLE_ARN=$(aws iam get-role --role-name "$TASK_ROLE_NAME" --query "Role.Arn" --output text)
    fi

    dynamodb_policy=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:DescribeTable",
        "dynamodb:BatchWriteItem",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:$AWS_REGION:$AWS_ACCOUNT_ID:table/$LEADS_DDB_TABLE",
        "arn:aws:dynamodb:$AWS_REGION:$AWS_ACCOUNT_ID:table/$RECOMMENDATIONS_DDB_TABLE",
        "arn:aws:dynamodb:$AWS_REGION:$AWS_ACCOUNT_ID:table/$HOMEPAGE_PROMPTS_DDB_TABLE"
      ]
    }
  ]
}
EOF
)

    aws iam put-role-policy \
        --role-name "$TASK_ROLE_NAME" \
        --policy-name "${APP_NAME}DynamoDbAccess" \
        --policy-document "$dynamodb_policy" >/dev/null
}

get_default_vpc() {
    aws ec2 describe-vpcs \
        --filters Name=isDefault,Values=true \
        --query "Vpcs[0].VpcId" --output text --region "$AWS_REGION" 2>/dev/null || echo ""
}

get_public_subnets() {
    local vpc_id="$1"
    aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$vpc_id" "Name=map-public-ip-on-launch,Values=true" \
        --query "Subnets[*].SubnetId" --output text --region "$AWS_REGION" 2>/dev/null | tr '\t' ','
}

wait_for_service_stable() {
    echo "  ⏳ 等待服务稳定（最多 5 分钟）..."
    aws ecs wait services-stable \
        --cluster "$ECS_CLUSTER_NAME" \
        --services "$ECS_SERVICE_NAME" \
        --region "$AWS_REGION" 2>/dev/null || true
}

get_alb_dns() {
    if [ -n "${ALB_ARN:-}" ]; then
        aws elbv2 describe-load-balancers \
            --load-balancer-arns "$ALB_ARN" \
            --query "LoadBalancers[0].DNSName" --output text --region "$AWS_REGION" 2>/dev/null || echo ""
    fi
}

# ══════════════════════════════════════════════════════════
#  推送镜像到 ECR
# ══════════════════════════════════════════════════════════

push_to_ecr() {
    echo "══ 推送镜像到 ECR ══"

    # 确保仓库存在
    aws ecr describe-repositories --repository-names "$ECR_REPO_NAME" --region "$AWS_REGION" >/dev/null 2>&1 || {
        echo "  📦 创建 ECR 仓库..."
        aws ecr create-repository --repository-name "$ECR_REPO_NAME" --region "$AWS_REGION" >/dev/null
    }

    # 登录 ECR
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "$ECR_REGISTRY" 2>/dev/null

    docker tag "$IMAGE_NAME:latest" "$ECR_IMAGE"

    echo "  📤 推送中..."
    docker push "$ECR_IMAGE"
    echo "  ✅ 推送完成: $ECR_IMAGE"
}

# ══════════════════════════════════════════════════════════
#  命令: status
# ══════════════════════════════════════════════════════════

cmd_status() {
    load_config
    if [ -z "${ECS_CLUSTER_NAME:-}" ]; then
        echo "❌ 尚未部署。请先运行: $0 --build"
        exit 1
    fi

    echo ""
    echo "═══ ECS 服务状态 ═══"
    print_context
    echo ""
    aws ecs describe-services \
        --cluster "$ECS_CLUSTER_NAME" \
        --services "$ECS_SERVICE_NAME" \
        --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}" \
        --output table --region "$AWS_REGION" 2>/dev/null

    local dns
    dns=$(get_alb_dns)
    if [ -n "${CUSTOM_DOMAIN:-}" ]; then
        echo "" && echo "  🌐 访问地址: https://$CUSTOM_DOMAIN"
    elif [ -n "$dns" ]; then
        echo "" && echo "  🌐 访问地址: http://$dns"
    fi
    echo ""
}

# ══════════════════════════════════════════════════════════
#  命令: logs
# ══════════════════════════════════════════════════════════

cmd_logs() {
    load_config
    local since="${1:-1h}"
    echo "📋 最近日志 (since=$since, Ctrl+C 退出):"
    echo "   提示: $0 logs 24h  查看最近 24 小时"
    aws logs tail "/ecs/$APP_NAME" --follow --since "$since" --region "$AWS_REGION" 2>/dev/null || {
        echo "  查看日志: AWS Console → CloudWatch → Log groups → /ecs/$APP_NAME"
    }
}

# ══════════════════════════════════════════════════════════
#  命令: destroy
# ══════════════════════════════════════════════════════════

cmd_destroy() {
    load_config
    if [ -z "${ECS_CLUSTER_NAME:-}" ]; then
        echo "没有可删除的资源。"; exit 0
    fi

    echo ""
    echo "⚠️  即将删除当前配置文件记录的新账号资源:"
    print_context
    echo ""
    echo "   ECS Service、Cluster、ALB、Target Group，以及本地部署配置文件。"
    echo "   注意：DynamoDB、ECR、CloudWatch Logs、IAM Role 不会由此命令删除。"
    echo ""
    read -r -p "请输入当前 AWS Account ID 以确认删除: " confirm
    [ "$confirm" = "$AWS_ACCOUNT_ID" ] || { echo "已取消。"; exit 0; }

    aws ecs update-service --cluster "$ECS_CLUSTER_NAME" --service "$ECS_SERVICE_NAME" --desired-count 0 --region "$AWS_REGION" >/dev/null 2>&1 || true
    aws ecs delete-service --cluster "$ECS_CLUSTER_NAME" --service "$ECS_SERVICE_NAME" --force --region "$AWS_REGION" >/dev/null 2>&1 || true
    [ -n "${ALB_ARN:-}" ] && aws elbv2 delete-load-balancer --load-balancer-arn "$ALB_ARN" --region "$AWS_REGION" >/dev/null 2>&1 || true
    sleep 5
    [ -n "${TG_ARN:-}" ] && aws elbv2 delete-target-group --target-group-arn "$TG_ARN" --region "$AWS_REGION" >/dev/null 2>&1 || true
    aws ecs delete-cluster --cluster "$ECS_CLUSTER_NAME" --region "$AWS_REGION" >/dev/null 2>&1 || true
    rm -f "$DEPLOY_CONFIG"
    echo "✅ 资源已删除。"
}

# ══════════════════════════════════════════════════════════
#  命令: setup-ssl <域名>
# ══════════════════════════════════════════════════════════

cmd_setup_ssl() {
    local domain="$1"
    load_config

    if [ -z "${ALB_ARN:-}" ]; then
        echo "❌ 尚未部署。请先运行: $0 --build"
        exit 1
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  配置自定义域名 + HTTPS"
    echo "  域名: $domain"
    echo "═══════════════════════════════════════════════════════"

    # ── 1. 申请 ACM 证书 ──
    echo ""
    echo "══ 1/5 申请 SSL 证书 ══"

    if [ -n "${CERT_ARN:-}" ]; then
        local cert_status
        cert_status=$(aws acm describe-certificate \
            --certificate-arn "$CERT_ARN" \
            --query "Certificate.Status" --output text \
            --region "$AWS_REGION" 2>/dev/null || echo "NOT_FOUND")
        if [ "$cert_status" = "ISSUED" ]; then
            echo "  ✅ 证书已存在且有效: $CERT_ARN"
        elif [ "$cert_status" = "PENDING_VALIDATION" ]; then
            echo "  ⏳ 证书已申请，等待 DNS 验证..."
        else
            echo "  ⚠️  旧证书状态异常 ($cert_status)，重新申请..."
            CERT_ARN=""
        fi
    fi

    if [ -z "${CERT_ARN:-}" ]; then
        CERT_ARN=$(aws acm request-certificate \
            --domain-name "$domain" \
            --validation-method DNS \
            --query "CertificateArn" --output text \
            --region "$AWS_REGION")
        echo "  📦 证书已申请: $CERT_ARN"
        sleep 3
    fi

    # ── 2. 显示 DNS 验证记录 ──
    echo ""
    echo "══ 2/5 DNS 验证 ══"
    echo ""

    local validation_info
    validation_info=$(aws acm describe-certificate \
        --certificate-arn "$CERT_ARN" \
        --query "Certificate.DomainValidationOptions[0].ResourceRecord" \
        --output json --region "$AWS_REGION" 2>/dev/null)

    local cname_name cname_value
    cname_name=$(echo "$validation_info" | python3 -c "import sys,json; print(json.load(sys.stdin)['Name'])" 2>/dev/null || echo "")
    cname_value=$(echo "$validation_info" | python3 -c "import sys,json; print(json.load(sys.stdin)['Value'])" 2>/dev/null || echo "")

    if [ -z "$cname_name" ]; then
        echo "  ⏳ 验证记录生成中，稍后请重新运行此命令..."
        CUSTOM_DOMAIN="$domain"
        save_config
        exit 0
    fi

    echo "  请在你的 DNS 管理面板添加以下 CNAME 记录来验证域名所有权："
    echo ""
    echo "  ┌──────────────────────────────────────────────────"
    echo "  │ 类型:   CNAME"
    echo "  │ 名称:   $cname_name"
    echo "  │ 值:     $cname_value"
    echo "  └──────────────────────────────────────────────────"
    echo ""

    local cert_status
    cert_status=$(aws acm describe-certificate \
        --certificate-arn "$CERT_ARN" \
        --query "Certificate.Status" --output text \
        --region "$AWS_REGION" 2>/dev/null)

    if [ "$cert_status" = "PENDING_VALIDATION" ]; then
        echo "  ⏳ 等待证书验证（添加 DNS 记录后通常需要 5-30 分钟）..."
        echo "     按 Ctrl+C 中断等待，稍后重新运行 setup-ssl 继续"
        echo ""

        CUSTOM_DOMAIN="$domain"
        save_config

        local wait_count=0
        while [ "$cert_status" = "PENDING_VALIDATION" ] && [ $wait_count -lt 60 ]; do
            sleep 15
            wait_count=$((wait_count + 1))
            cert_status=$(aws acm describe-certificate \
                --certificate-arn "$CERT_ARN" \
                --query "Certificate.Status" --output text \
                --region "$AWS_REGION" 2>/dev/null)
            printf "\r  已等待 %d 秒... (状态: %s)   " $((wait_count * 15)) "$cert_status"
        done
        echo ""

        if [ "$cert_status" != "ISSUED" ]; then
            echo ""
            echo "  ⚠️  证书尚未通过验证 (状态: $cert_status)"
            echo "     请确认 DNS 记录已添加，稍后重新运行:"
            echo "     $0 setup-ssl $domain"
            exit 0
        fi
    fi

    if [ "$cert_status" != "ISSUED" ]; then
        echo "  ❌ 证书状态异常: $cert_status"
        exit 1
    fi

    echo "  ✅ 证书已签发！"

    # ── 3. ALB 添加 HTTPS 监听器 ──
    echo ""
    echo "══ 3/5 配置 HTTPS 监听器 ══"

    local existing_https
    existing_https=$(aws elbv2 describe-listeners \
        --load-balancer-arn "$ALB_ARN" \
        --query "Listeners[?Protocol=='HTTPS'].ListenerArn" \
        --output text --region "$AWS_REGION" 2>/dev/null || echo "")

    if [ -n "$existing_https" ] && [ "$existing_https" != "None" ]; then
        echo "  ✅ HTTPS 监听器已存在，更新证书..."
        aws elbv2 modify-listener \
            --listener-arn "$existing_https" \
            --certificates "CertificateArn=$CERT_ARN" \
            --region "$AWS_REGION" >/dev/null
    else
        aws elbv2 create-listener \
            --load-balancer-arn "$ALB_ARN" \
            --protocol HTTPS --port 443 \
            --certificates "CertificateArn=$CERT_ARN" \
            --default-actions "Type=forward,TargetGroupArn=$TG_ARN" \
            --region "$AWS_REGION" >/dev/null
        echo "  ✅ HTTPS 监听器已创建（端口 443）"
    fi

    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" \
        --protocol tcp --port 443 --cidr 0.0.0.0/0 \
        --region "$AWS_REGION" 2>/dev/null || true

    # HTTP → HTTPS 重定向
    local http_listener
    http_listener=$(aws elbv2 describe-listeners \
        --load-balancer-arn "$ALB_ARN" \
        --query "Listeners[?Protocol=='HTTP'].ListenerArn" \
        --output text --region "$AWS_REGION" 2>/dev/null || echo "")

    if [ -n "$http_listener" ] && [ "$http_listener" != "None" ]; then
        aws elbv2 modify-listener \
            --listener-arn "$http_listener" \
            --default-actions 'Type=redirect,RedirectConfig={Protocol=HTTPS,Port=443,StatusCode=HTTP_301}' \
            --region "$AWS_REGION" >/dev/null
        echo "  ✅ HTTP → HTTPS 自动跳转已启用"
    fi

    # ── 4. 保存配置 ──
    CUSTOM_DOMAIN="$domain"
    save_config

    # ── 5. 提示后续操作 ──
    local alb_dns
    alb_dns=$(get_alb_dns)

    echo ""
    echo "══ 4/5 配置 DNS 解析 ══"
    echo ""
    echo "  请在你的 DNS 管理面板添加以下记录，将域名指向 ALB："
    echo ""
    echo "  ┌──────────────────────────────────────────────────"
    echo "  │ 类型:   CNAME"
    echo "  │ 名称:   $domain"
    echo "  │ 值:     $alb_dns"
    echo "  └──────────────────────────────────────────────────"
    echo ""

    echo "══ 5/5 OpenAI 域名白名单 ══"
    echo ""
    echo "  请在 OpenAI 平台添加你的域名到白名单（ChatKit 需要）："
    echo ""
    echo "  1. 打开 https://platform.openai.com/settings/organization/security/domain-allowlist"
    echo "  2. 点击 Add Domain，添加: $domain"
    echo ""

    echo "══ 更新 PUBLIC_BASE_URL ══"
    echo ""
    if [ -f "$ENV_FILE" ]; then
        if grep -q "^PUBLIC_BASE_URL=" "$ENV_FILE"; then
            sed -i.bak "s|^PUBLIC_BASE_URL=.*|PUBLIC_BASE_URL=https://$domain|" "$ENV_FILE"
            rm -f "${ENV_FILE}.bak"
        else
            echo "PUBLIC_BASE_URL=https://$domain" >> "$ENV_FILE"
        fi
        echo "  ✅ 已更新 apps/rag-api/.env 中的 PUBLIC_BASE_URL=https://$domain"
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  ✅ HTTPS 配置完成！"
    echo ""
    echo "  完成上述 DNS 和 OpenAI 白名单配置后，重新部署生效:"
    echo ""
    echo "    $0 --build"
    echo ""
    echo "  访问地址: https://$domain"
    echo "═══════════════════════════════════════════════════════"
}

# ══════════════════════════════════════════════════════════
#  命令: deploy
# ══════════════════════════════════════════════════════════

cmd_deploy() {
    load_config

    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  EAI Robot — 推送到 AWS 并部署"
    echo "═══════════════════════════════════════════════════════"
    echo ""
    print_context
    echo ""

    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ 环境变量文件不存在: $ENV_FILE"
        exit 1
    fi

    # ── 1. 推送镜像 ──
    echo ""
    push_to_ecr

    # ── 2. IAM 角色 ──
    echo ""
    echo "══ 配置 IAM 角色 ══"
    if ! aws iam get-role --role-name ecsTaskExecutionRole &>/dev/null; then
        echo "  📦 创建 ECS 执行角色..."
        aws iam create-role --role-name ecsTaskExecutionRole \
            --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
        aws iam attach-role-policy --role-name ecsTaskExecutionRole \
            --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy >/dev/null
    fi
    # IAM role names can have a path (for example, service-role/). Resolve the
    # ARN rather than constructing it, otherwise ECS cannot assume the role.
    local execution_role_arn
    execution_role_arn=$(aws iam get-role --role-name ecsTaskExecutionRole --query "Role.Arn" --output text)
    aws iam put-role-policy --role-name ecsTaskExecutionRole \
        --policy-name CloudWatchLogsCreateGroup \
        --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"logs:CreateLogGroup","Resource":"*"}]}' 2>/dev/null || true
    ensure_task_role
    echo "  ✅ IAM 角色就绪"

    aws logs create-log-group --log-group-name "/ecs/$APP_NAME" --region "$AWS_REGION" 2>/dev/null || true
    ensure_dynamodb_tables

    # ── 3. Task Definition ──
    echo ""
    echo "══ 注册 Task Definition ══"
    TASK_FAMILY="${TASK_FAMILY:-$APP_NAME}"
    local env_json
    env_json=$(parse_env_file)
    env_json=$(build_task_env_json "$env_json")

    cat > /tmp/ecs-task-def.json << TASKDEF
{
    "family": "$TASK_FAMILY",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "$CPU",
    "memory": "$MEMORY",
    "executionRoleArn": "$execution_role_arn",
    "taskRoleArn": "$TASK_ROLE_ARN",
    "containerDefinitions": [{
        "name": "$APP_NAME",
        "image": "$ECR_IMAGE",
        "essential": true,
        "portMappings": [{"containerPort": $CONTAINER_PORT, "protocol": "tcp"}],
        "environment": $env_json,
        "healthCheck": {
            "command": ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')\""],
            "interval": 30, "timeout": 5, "retries": 3, "startPeriod": 15
        },
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "/ecs/$APP_NAME",
                "awslogs-region": "$AWS_REGION",
                "awslogs-stream-prefix": "app",
                "awslogs-create-group": "true"
            }
        }
    }],
    "runtimePlatform": {"cpuArchitecture": "X86_64", "operatingSystemFamily": "LINUX"}
}
TASKDEF

    aws ecs register-task-definition --cli-input-json file:///tmp/ecs-task-def.json --region "$AWS_REGION" >/dev/null
    echo "  ✅ Task Definition: $TASK_FAMILY"

    # Set CloudWatch log retention to 30 days to prevent unbounded growth
    aws logs put-retention-policy \
        --log-group-name "/ecs/$APP_NAME" \
        --retention-in-days 30 \
        --region "$AWS_REGION" 2>/dev/null || true

    # ── 已部署过？直接滚动更新 ──
    if [ -n "${ECS_SERVICE_NAME:-}" ]; then
        echo ""
        echo "══ 滚动更新 ══"
        aws ecs update-service \
            --cluster "$ECS_CLUSTER_NAME" --service "$ECS_SERVICE_NAME" \
            --task-definition "$TASK_FAMILY" --force-new-deployment \
            --region "$AWS_REGION" >/dev/null
        echo "  ✅ 更新已触发"
        wait_for_service_stable
        save_config
        local dns; dns=$(get_alb_dns)
        local url
        if [ -n "${CUSTOM_DOMAIN:-}" ]; then url="https://$CUSTOM_DOMAIN"; else url="http://$dns"; fi
        echo ""
        echo "═══════════════════════════════════════════════════════"
        echo "  ✅ 更新完成！访问地址: $url"
        echo "═══════════════════════════════════════════════════════"
        return
    fi

    # ── 4. 首次部署：创建基础设施 ──
    echo ""
    echo "══ 创建网络和负载均衡器 ══"

    VPC_ID="${DEPLOY_VPC_ID:-$(get_default_vpc)}"
    if [ -z "$VPC_ID" ] || [ "$VPC_ID" = "None" ]; then
        echo "❌ 未找到默认 VPC。"
        echo "   如需使用指定网络，请设置:"
        echo "   DEPLOY_VPC_ID=vpc-xxx DEPLOY_SUBNET_IDS=subnet-a,subnet-b $0 --build"
        exit 1
    fi
    SUBNET_IDS="${DEPLOY_SUBNET_IDS:-$(get_public_subnets "$VPC_ID")}"
    if [ -z "$SUBNET_IDS" ]; then
        echo "❌ 未找到公有子网。"
        echo "   如需使用指定子网，请设置:"
        echo "   DEPLOY_SUBNET_IDS=subnet-a,subnet-b $0 --build"
        exit 1
    fi
    echo "  VPC: $VPC_ID | 子网: $SUBNET_IDS"

    # 安全组
    SG_ID=$(aws ec2 create-security-group \
        --group-name "${APP_NAME}-sg" --description "$APP_NAME" \
        --vpc-id "$VPC_ID" --query "GroupId" --output text --region "$AWS_REGION" 2>/dev/null || \
        aws ec2 describe-security-groups \
            --filters "Name=group-name,Values=${APP_NAME}-sg" "Name=vpc-id,Values=$VPC_ID" \
            --query "SecurityGroups[0].GroupId" --output text --region "$AWS_REGION")
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" \
        --protocol tcp --port 80 --cidr 0.0.0.0/0 --region "$AWS_REGION" 2>/dev/null || true
    echo "  ✅ 安全组: $SG_ID"

    # ALB
    local subnet_args; subnet_args=$(echo "$SUBNET_IDS" | tr ',' ' ')
    ALB_ARN=$(aws elbv2 create-load-balancer --name "${APP_NAME}-alb" \
        --subnets $subnet_args --security-groups "$SG_ID" \
        --scheme internet-facing --type application \
        --query "LoadBalancers[0].LoadBalancerArn" --output text --region "$AWS_REGION")

    TG_ARN=$(aws elbv2 create-target-group --name "${APP_NAME}-tg" \
        --protocol HTTP --port $CONTAINER_PORT --vpc-id "$VPC_ID" --target-type ip \
        --health-check-path "/health" --health-check-interval-seconds 30 \
        --healthy-threshold-count 2 --unhealthy-threshold-count 3 \
        --query "TargetGroups[0].TargetGroupArn" --output text --region "$AWS_REGION")

    aws elbv2 create-listener --load-balancer-arn "$ALB_ARN" \
        --protocol HTTP --port 80 \
        --default-actions "Type=forward,TargetGroupArn=$TG_ARN" --region "$AWS_REGION" >/dev/null
    echo "  ✅ ALB 已创建"

    # ── 5. ECS Cluster + Service ──
    echo ""
    echo "══ 创建 ECS 集群和服务 ══"
    ECS_CLUSTER_NAME="${APP_NAME}-cluster"
    ECS_SERVICE_NAME="${APP_NAME}-service"

    aws ecs create-cluster --cluster-name "$ECS_CLUSTER_NAME" --region "$AWS_REGION" >/dev/null 2>&1 || true

    local svc_status
    svc_status=$(aws ecs describe-services \
        --cluster "$ECS_CLUSTER_NAME" --services "$ECS_SERVICE_NAME" \
        --query "services[?status!='INACTIVE'].status" --output text --region "$AWS_REGION" 2>/dev/null || true)

    if [ -n "$svc_status" ]; then
        echo "  ⚠️  Service 已存在 (${svc_status})，执行 update-service..."
        aws ecs update-service \
            --cluster "$ECS_CLUSTER_NAME" --service "$ECS_SERVICE_NAME" \
            --task-definition "$TASK_FAMILY" --desired-count 1 --force-new-deployment \
            --region "$AWS_REGION" >/dev/null
        echo "  ✅ ECS Service 已更新"
    else
        aws ecs create-service \
            --cluster "$ECS_CLUSTER_NAME" --service-name "$ECS_SERVICE_NAME" \
            --task-definition "$TASK_FAMILY" --desired-count 1 --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
            --load-balancers "targetGroupArn=$TG_ARN,containerName=$APP_NAME,containerPort=$CONTAINER_PORT" \
            --region "$AWS_REGION" >/dev/null
        echo "  ✅ ECS Service 已创建"
    fi

    save_config
    wait_for_service_stable

    local dns; dns=$(get_alb_dns)
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  ✅ 首次部署完成！"
    echo ""
    echo "  🌐 访问地址: http://$dns"
    echo ""
    echo "  后续更新:     $0 --build"
    echo "  配置 HTTPS:   $0 setup-ssl <你的域名>"
    echo "  查看状态:     $0 status"
    echo "  查看日志:     $0 logs"
    echo ""
    echo "  ⚠️  ChatKit 需要 HTTPS 才能在线上工作"
    echo "  请尽快运行 setup-ssl 配置自定义域名和 HTTPS"
    echo "═══════════════════════════════════════════════════════"
}

# ══════════════════════════════════════════════════════════
#  入口
# ══════════════════════════════════════════════════════════

show_usage() {
    echo "Usage: $0 [global options] <command>"
    echo ""
    echo "Global options:"
    echo "  --profile <name>             使用指定 AWS CLI profile"
    echo "  --region <region>            覆盖 AWS region（默认 us-east-1）"
    echo "  --config <path>              覆盖部署配置文件（默认 .deploy-config-new-account）"
    echo ""
    echo "Commands:"
    echo "  --build                构建镜像 + 推送 + 部署（一步到位）"
    echo "  setup-ssl <域名>       配置自定义域名 + HTTPS（首次）"
    echo "  status                 查看 ECS 服务状态"
    echo "  logs [时长]            查看容器日志（默认 1h，如 24h）"
    echo "  destroy                删除所有 AWS 资源"
    echo ""
    echo "Examples:"
    echo "  $0 --build"
    echo "  $0 --profile eai-robot-new --build"
    echo "  DEPLOY_VPC_ID=vpc-xxx DEPLOY_SUBNET_IDS=subnet-a,subnet-b $0 --profile eai-robot-new --build"
}

if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

while [ $# -gt 0 ]; do
    case "$1" in
        --profile)
            AWS_PROFILE="${2:-}"
            if [ -z "$AWS_PROFILE" ]; then echo "❌ --profile 需要参数"; exit 1; fi
            export AWS_PROFILE
            shift 2
            ;;
        --region)
            AWS_REGION="${2:-}"
            if [ -z "$AWS_REGION" ]; then echo "❌ --region 需要参数"; exit 1; fi
            export AWS_DEFAULT_REGION="$AWS_REGION"
            shift 2
            ;;
        --config)
            DEPLOY_CONFIG="${2:-}"
            if [ -z "$DEPLOY_CONFIG" ]; then echo "❌ --config 需要参数"; exit 1; fi
            shift 2
            ;;
        --expected-account)
            if [ "${2:-}" != "$EXPECTED_AWS_ACCOUNT_ID" ]; then
                echo "❌ 此脚本已固定为 AWS 账号 $EXPECTED_AWS_ACCOUNT_ID，不能覆盖。"
                exit 1
            fi
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

ACTION="$1"
shift

case "$ACTION" in
    --build)
        check_prerequisites

        echo ""
        echo "══ 构建 Chat SDK (release) ══"
        VITE_CHAT_SERVICE_ORIGIN="$PRODUCTION_CHAT_SERVICE_ORIGIN" \
            "$SCRIPT_DIR/packages/chat-sdk/build.sh" release

        echo ""
        echo "══ 构建 Docker 镜像 ══"
        echo "  🌐 Chat 服务域名: $PRODUCTION_CHAT_SERVICE_ORIGIN"
        echo ""
        echo "  🔨 构建中（目标平台: linux/amd64）..."
        docker buildx build --platform linux/amd64 \
            --build-arg VITE_CHAT_SERVICE_ORIGIN="$PRODUCTION_CHAT_SERVICE_ORIGIN" \
            --build-arg VITE_CHATKIT_DOMAIN_KEY="$CHATKIT_DOMAIN_KEY" \
            -t "$IMAGE_NAME" -f Dockerfile "$SCRIPT_DIR"
        echo ""
        echo "  ✅ Docker 镜像构建完成: $IMAGE_NAME"

        cmd_deploy
        ;;
    setup-ssl)
        DOMAIN="${1:-}"
        if [ -z "$DOMAIN" ]; then
            echo "❌ 请指定域名。用法: $0 setup-ssl your.domain.com"
            exit 1
        fi
        check_prerequisites
        cmd_setup_ssl "$DOMAIN"
        ;;
    status)
        load_config 2>/dev/null || { echo "❌ 尚未部署"; exit 1; }
        cmd_status
        ;;
    logs)
        load_config 2>/dev/null || { echo "❌ 尚未部署"; exit 1; }
        cmd_logs "$@"
        ;;
    destroy)
        load_config 2>/dev/null || { echo "❌ 尚未部署"; exit 1; }
        cmd_destroy
        ;;
    *)
        echo "❌ 未知命令: $ACTION"
        echo ""
        show_usage
        exit 1
        ;;
esac
