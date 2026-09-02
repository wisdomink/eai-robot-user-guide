# EAI Robot User Guide — Docker 构建与 AWS ECS 部署指南

---

## 目录

1. [项目架构](#1-项目架构)
2. [前置准备](#2-前置准备)
3. [本地 Docker 测试](#3-本地-docker-测试)
4. [一键部署到 AWS ECS](#4-一键部署到-aws-ecs)
5. [后续更新](#5-后续更新)
6. [自定义域名](#6-自定义域名)
7. [环境变量参考](#7-环境变量参考)
8. [脚本命令速查](#8-脚本命令速查)
9. [常见问题](#9-常见问题)

---

## 1. 项目架构

本项目打包为 **单个 Docker 镜像**，对外只暴露 80 端口：

```
                    ┌──────────────────────────────────────┐
                    │         单个 Docker 容器              │
                    │                                      │
  浏览器 ── :80 ──▶ │  ┌─────────┐      ┌──────────────┐  │
                    │  │  nginx   │ 代理  │  uvicorn     │  │
                    │  │  静态文件 │─────▶│  (FastAPI)   │  │
                    │  │  :80     │      │  :8000       │  │
                    │  └─────────┘      └──────────────┘  │
                    │         supervisord 进程管理          │
                    └──────────────────────────────────────┘
```

---

## 2. 前置准备

### 2.1 安装 Docker Desktop

下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)，确保其正在运行。

### 2.2 安装 AWS CLI

```bash
brew install awscli
```

### 2.3 配置 AWS 凭证

需要你的 AWS Access Key ID 和 Secret Access Key。
获取方式：登录 AWS Console → 右上角用户名 → Security credentials → Create access key

本地部署推荐使用项目根目录的 `.env` 文件：

```bash
cp .env.example .env
# 编辑 .env，填入 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY
```

`.env` 不会被提交到 Git，也不会被包含进 Docker 镜像。部署脚本会校验当前身份是否为指定 AWS 账号。

也可以通过以下方式配置凭证：

```bash
# AWS CLI Profile
aws configure
```

### 2.4 配置环境变量

确保 `apps/rag-api/.env` 文件已填入所有必要的值（OPENAI_API_KEY 等）。
如果是全新项目，先从模板创建：

```bash
cp apps/rag-api/.env.example apps/rag-api/.env
# 编辑填入实际值
```

---

## 3. 本地 Docker 测试

在部署到 AWS 之前，建议先在本地验证：

```bash
# 构建并启动
docker compose up --build -d

# 验证
curl http://localhost/health    # 应返回 {"status":"ok"}
open http://localhost            # 浏览器访问

# 停止
docker compose down
```

---

## 4. 一键部署到 AWS ECS

### 首次部署

只需一条命令，脚本会自动完成所有工作：

```bash
./aws-deploy.sh
```

脚本自动执行的步骤：

1. **构建 Docker 镜像**（Mac Apple Silicon 自动交叉编译为 amd64）
2. **推送到 AWS ECR**（自动创建仓库、登录、推送）
3. **创建 IAM 角色**（ECS 执行角色）
4. **注册 Task Definition**（从 `apps/rag-api/.env` 读取环境变量）
5. **创建网络基础设施**（安全组、ALB、Target Group）
6. **创建 ECS 集群和服务**（Fargate 启动类型）
7. **等待服务就绪**并输出公网访问地址

完成后你会看到：

```
  ✅ 首次部署完成！

  🌐 访问地址: http://eai-robot-alb-xxx.us-east-1.elb.amazonaws.com

  后续更新只需再次运行: ./aws-deploy.sh
```

这个 `elb.amazonaws.com` 域名就是 AWS 分配的公网地址，可以直接在浏览器访问。

---

## 5. 后续更新

修改代码后，再次运行同一命令即可滚动更新：

```bash
./aws-deploy.sh
```

脚本会检测到已有部署，自动执行：
1. 构建最新镜像并推送
2. 更新 Task Definition（包含最新环境变量）
3. 触发 ECS 滚动更新（零停机）

---

## 6. 自定义域名 + HTTPS

> **重要**：ChatKit 需要 HTTPS 才能在线上正常工作（`localhost` 除外）。
> 部署到 AWS 后必须配置自定义域名 + HTTPS。

### 一键配置

准备好域名后，运行：

```bash
./aws-deploy.sh setup-ssl docs.yourcompany.com
```

脚本会自动完成：

1. 在 AWS ACM 申请免费 SSL 证书
2. 输出 DNS 验证记录（需要你手动添加到 DNS）
3. 等待证书验证通过
4. 给 ALB 添加 HTTPS 监听器（443 端口）
5. 配置 HTTP → HTTPS 自动跳转
6. 更新 `apps/rag-api/.env` 中的 `PUBLIC_BASE_URL`

### 需要手动完成的部分

脚本运行过程中会提示你完成两项手动操作：

**a) DNS 配置（在你的域名服务商处）**

需要添加两条 CNAME 记录：

| 用途 | 类型 | 名称 | 值 |
|------|------|------|-----|
| 证书验证 | CNAME | `_xxx.docs.yourcompany.com` | `_xxx.acm-validations.aws` |
| 域名解析 | CNAME | `docs` | `eai-robot-alb-xxx.elb.amazonaws.com` |

（实际值以脚本输出为准）

**b) OpenAI 域名白名单**

1. 打开 https://platform.openai.com/settings/organization/security/domain-allowlist
2. 添加你的域名：`docs.yourcompany.com`

### 配置完成后重新部署

```bash
./aws-deploy.sh --build
```

访问 `https://docs.yourcompany.com` 验证一切正常。

### 如果中途中断

`setup-ssl` 命令支持断点续做。如果证书验证超时或你按了 Ctrl+C，
稍后重新运行同一命令即可从上次的位置继续：

```bash
./aws-deploy.sh setup-ssl docs.yourcompany.com
```

---

## 7. 环境变量参考

| 变量名 | 必填 | 说明 |
|--------|:----:|------|
| `OPENAI_API_KEY` | ✅ | OpenAI API Key |
| `LLM_MODEL` | — | LLM 模型（默认 gpt-5） |
| `OPENAI_VECTOR_STORE_MASTER_ULTRA_ID` | — | Master Ultra 向量库 ID |
| `OPENAI_VECTOR_STORE_FUTURIST_ULTRA_ID` | — | Futurist Ultra 向量库 ID |
| `OPENAI_VECTOR_STORE_AEGIS_ULTRA_ID` | — | Aegis Ultra 向量库 ID |
| `OPENAI_VECTOR_STORE_AEGIS_EDU_ID` | — | Aegis EDU 向量库 ID |
| `OPENAI_VECTOR_STORE_ROBOT_ALL_ID` | — | 全产品统一向量库 ID |
| `PUBLIC_BASE_URL` | — | 公网 URL（部署后需更新为实际域名） |

---

## 8. 脚本命令速查

### aws-deploy.sh — AWS 部署

| 命令 | 说明 |
|------|------|
| `./aws-deploy.sh --build` | 构建镜像 + 推送 + 部署（一步到位） |
| `./aws-deploy.sh setup-ssl <域名>` | 配置自定义域名 + HTTPS |
| `./aws-deploy.sh status` | 查看 ECS 服务状态 |
| `./aws-deploy.sh logs` | 查看容器日志 |
| `./aws-deploy.sh destroy` | 删除所有 AWS 资源 |

### docker compose — 本地测试

| 命令 | 说明 |
|------|------|
| `docker compose up --build -d` | 本地构建并启动 |
| `docker compose logs -f` | 查看日志 |
| `docker compose down` | 停止 |
| `docker compose exec app sh` | 进入容器 |

---

## 9. 常见问题

### Q: Docker 构建时拉取镜像超时

优先使用官方 Docker Hub。若你之前在 `~/.docker/daemon.json` 里配置过 `registry-mirrors`，请删除该字段后重启 Docker Desktop。

### Q: AWS Region 是什么？

当前服务部署在 `us-east-1`（弗吉尼亚北部）；根目录 `.env` 中应设置 `AWS_REGION=us-east-1`。

### Q: 部署后环境变量改了怎么办？

修改 `apps/rag-api/.env` 后重新运行 `./aws-deploy.sh`，会自动注册新的 Task Definition 并滚动更新。

### Q: 是否需要再次运行 `setup-ssl`？

当前正式站通过 CloudFront 将请求转发到 ALB 的 HTTP 80 端口。不要在当前架构下运行 `./aws-deploy.sh setup-ssl ...`，该命令会把 HTTP 监听器改为 HTTPS 跳转，导致 CloudFront 源站请求异常。

### Q: 如何查看部署是否成功？

```bash
./aws-deploy.sh status
```

或登录 AWS Console → ECS → Clusters → eai-robot-cluster → Services 查看。

### Q: 如何删除所有 AWS 资源？

```bash
./aws-deploy.sh destroy
```

会删除 ECS Service、Cluster、ALB 等所有创建的资源。
