# EAI Robot User Manual (H5)

FF Robot 全系列产品用户手册，基于 React + Markdown 驱动的静态文档站，支持 SSG 预渲染与 AI 智能问答。

覆盖产品：**FF Master Ultra** · **FF Futurist Ultra** · **FF Aegis Ultra** · **FF Aegis EDU**

## 功能一览

| 功能 | 说明 |
|------|------|
| AI 智能问答 | 多 Agent 对话式问答，自动识别产品、检索手册内容并生成带引用跳转的回答 |
| AI 语义搜索 | 基于 OpenAI Vector Store Search API 的跨页面语义搜索，支持中英文混合查询 |
| 双模式 AI 对接 | 可通过环境变量切换「自托管后端」或「OpenAI Agent Builder 直连」两种模式 |
| 多产品导航 | 按产品线组织的侧边栏导航，支持产品间快速切换 |
| SPA 内部链接 | Markdown 中写路由路径，自动 SPA 导航 |
| 响应式布局 | Desktop 侧边栏常驻，Tablet/Mobile 抽屉式菜单 |
| Markdown 驱动 | 内容与代码完全分离，非技术人员可直接编辑 |
| SSG 预渲染 | 构建时为每个路由生成静态 HTML，支持 SEO |
| 打印友好 | `@media print` 优化，链接自动显示 URL |

## 技术栈

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19 | UI 框架 |
| Vite | 7 | 构建工具 + 开发服务器 |
| TypeScript | 5.9 | 类型安全 |
| Tailwind CSS | 4 | 样式系统（`@theme` 设计令牌） |
| React Router | 7 | 客户端路由（SPA） |
| marked | 17 | Markdown → HTML 渲染 |
| @openai/chatkit-react | 1.5+ | AI 对话面板 |

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.115+ | Web 框架 + SSE 流式响应 |
| OpenAI Agents SDK | 0.1+ | 多 Agent 工作流（Triage + Support Agents） |
| OpenAI ChatKit (Python) | 1.6+ | ChatKit 协议桥接 + 流式转换 |
| OpenAI Vector Store | — | 托管式文档检索（RAG + 语义搜索） |

后端详细文档见 [`rag_server/README.md`](rag_server/README.md)。

## 项目结构

```
eai-robot-user-guide/
├── README.md
├── CLAUDE.md                    # 项目约定 + Figma MCP 集成规则
├── index.html                   # Vite 入口（含 ChatKit JS CDN）
├── package.json
├── vite.config.ts               # Vite 配置 + 后端代理规则
├── client_run.sh                # 前端一键启动脚本
├── deploy.sh                    # 测试环境一键部署（前端 + 后端）
├── aws-deploy.sh                # AWS 部署脚本
├── docker-build.sh              # Docker 构建脚本
│
├── scripts/
│   ├── convert.mjs              # 源文档 → Markdown 转换（Master Ultra）
│   ├── convert-futurist.mjs     # Futurist Ultra 转换
│   ├── convert-aegis.mjs        # Aegis Ultra 转换
│   ├── convert-aegisedu.mjs     # Aegis EDU 转换
│   └── prerender.mjs            # SSG 预渲染脚本
│
├── rag_server/                  # AI 后端（独立 Python 服务）
│   ├── app/
│   │   ├── main.py              # 入口：/chatkit、/api/chatkit/session、/search
│   │   ├── core/config.py       # 配置（环境变量 + 路径）
│   │   └── services/
│   │       ├── chatkit_handler.py   # 多 Agent 工作流 + ChatKit 桥接
│   │       └── instructions/*.md   # 各 Agent 的 Prompt 模板
│   ├── eval/                    # RAG 评测脚本
│   ├── create_vector_store.py  # Vector Store 同步（上传手册文档）
│   ├── agent-builder-design.md # Agent Builder 编排架构设计
│   ├── server_run.sh           # 一键启动脚本
│   └── README.md
│
├── public/images/               # 静态图片资源
│
└── src/
    ├── main.tsx                 # 客户端入口
    ├── entry-server.tsx        # SSG 服务端入口
    ├── App.tsx                 # 路由配置（从 sidebar.json 自动生成）
    ├── index.css               # Tailwind + 自定义样式
    │
    ├── content/                # 内容管理
    │   ├── sidebar.json        # 导航树配置（所有产品，按 productId 分组）
    │   ├── index.ts            # 内容注册表
    │   ├── chunks.ts           # 内容分块（按 ## 标题切分）
    │   └── pages/              # Markdown 页面
    │       ├── master-ultra/
    │       ├── futurist-ultra/
    │       ├── aegis-ultra/
    │       └── aegis-edu/
    │
    ├── components/
    │   ├── layout/             # Header、Sidebar、ContentLayout、MobileMenuDrawer
    │   ├── chat/
    │   │   └── ChatPanel.tsx   # ChatKit 对话面板（支持双模式）
    │   ├── markdown/
    │   │   └── MarkdownRenderer.tsx
    │   └── search/             # SearchBar、SearchDropdown、SearchInfoBar
    │
    ├── pages/
    │   └── MarkdownPage.tsx    # 通用 Markdown 页面
    │
    └── hooks/
        ├── useSearch.ts        # 搜索逻辑（精确 + 语义合并）
        ├── useSemanticSearch.ts # 语义搜索 Hook
        ├── useMediaQuery.ts    # 响应式断点
        └── useSidebarState.ts  # 侧边栏开关状态
```

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器（https://localhost:5173）
npm run dev
```

> 如需 AI 对话和语义搜索功能，还需启动 RAG Server，详见下方 [AI 智能问答](#ai-智能问答) 章节。

### 生产构建

```bash
npm run build     # 完整构建（含 SSG 预渲染）
npm run preview   # 预览构建结果
```

`npm run build` 依次执行：

1. **TypeScript 类型检查** — `tsc -b`
2. **客户端构建** — `vite build`（输出到 `dist/client/`）
3. **服务端构建** — `vite build --ssr`（输出到 `dist/server/`）
4. **SSG 预渲染** — `node scripts/prerender.mjs`（为每个路由生成静态 HTML）

## 环境变量

### 前端（Vite）

在 shell 或 `.env` 中配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `VITE_CHAT_MODE` | `backend` | AI 对话模式：`backend`（自托管）或 `agent-builder`（直连 OpenAI） |
| `VITE_CHATKIT_API_URL` | `/chatkit` | 后端 ChatKit 端点（仅 backend 模式使用） |
| `VITE_CHATKIT_SESSION_URL` | `/api/chatkit/session` | Session 创建端点（仅 agent-builder 模式使用） |
| `VITE_CHATKIT_DOMAIN_KEY` | `local-dev` | ChatKit 域名标识（仅 backend 模式使用） |

### 后端（RAG Server）

详见 [`rag_server/README.md` — 环境变量](rag_server/README.md#环境变量)。

## AI 智能问答

项目内置多 Agent 的 AI 对话功能，用户可在页面右侧打开 ChatPanel 提问。系统会自动识别产品、检索手册内容，生成带引用链接的结构化回答。

### 双模式架构

通过环境变量 `VITE_CHAT_MODE` / `CHAT_MODE` 切换两种 AI 对接方式：

**模式一：Backend（自托管后端）** — 默认

```
前端 ChatPanel (@openai/chatkit-react)
  │  ChatKit 协议（SSE 流式）
  ▼
RAG Server (FastAPI)
  │  Triage Agent → 语言检测 + 产品识别 + 查询扩写
  │  Support Agent → FileSearchTool + LLM 生成回答
  │  FFRobotConverter → file_citation 映射为 SPA 可跳转链接
  ▼
OpenAI API (Vector Store + LLM)
```

特点：完全自主可控，支持自定义引用跳转、图片 URL 重写等。

**模式二：Agent Builder（直连 OpenAI）**

```
前端 ChatPanel (@openai/chatkit-react)
  │  ① 请求 client_secret
  ▼
RAG Server → POST /api/chatkit/session → OpenAI API
  │  ② 返回 client_secret
  ▼
前端 ←→ OpenAI Agent Builder（聊天流量直连，不经后端）
```

特点：聊天逻辑由 OpenAI 平台托管，后端仅负责 session 创建。

### 本地启动

**方式一：分别启动**

```bash
# 终端 1：启动后端
cd rag_server && ./server_run.sh

# 终端 2：启动前端（默认 backend 模式）
./client_run.sh

# 或切换为 agent-builder 模式
VITE_CHAT_MODE=agent-builder ./client_run.sh
```

**方式二：一键部署**

```bash
./deploy.sh           # 启动所有服务
./deploy.sh status    # 查看状态
./deploy.sh stop      # 停止服务
./deploy.sh restart   # 重启服务
```

完整后端配置说明见 **[`rag_server/README.md`](rag_server/README.md)**。

## 内容管理

### 修改页面内容

直接编辑 `src/content/pages/` 下对应的 `.md` 文件即可。

### 新增页面

**第 1 步** — 创建 Markdown 文件，如 `src/content/pages/master-ultra/new-topic.md`

**第 2 步** — 在 `src/content/sidebar.json` 对应产品的 `sections` 中添加条目：

```json
{
  "title": "New Topic",
  "slug": "/master-ultra/new-topic",
  "file": "master-ultra/new-topic.md"
}
```

路由会根据 sidebar 自动生成，无需修改 `App.tsx`。

### 页面间跳转链接

```markdown
See also: [Safety Guidelines](/master-ultra/safety-guidelines)
```

以 `/` 开头的内部链接会通过 React Router 进行 SPA 导航。

### 添加图片

将图片放入 `public/images/`，在 Markdown 中引用：

```markdown
![Alt text](/images/your-image.png)
```

## 内容转换管道

从源文档（PDF / Word）生成 Markdown：

```bash
npm run convert              # Master Ultra：完整管道
npm run convert:futurist     # Futurist Ultra
npm run convert:aegis        # Aegis Ultra
npm run convert:aegisedu     # Aegis EDU
```

各命令支持 `:text`（仅文本）和 `:images`（仅图片）子命令。

## 设计系统

基于 Figma 设计稿的 Design Tokens：

- **字体**: Roboto（正文）、Rubik（标题/UI）
- **主色**: Navy `#171A20`、iOS Blue `#0A84FF`、Purple `#6965E0`
- **字号**: h1 36px、h2 30px、h3 17px、body 15px
- **断点**: Desktop ≥1024px、Tablet 768–1023px、Mobile <768px

## SEO

通过 SSG（Static Site Generation）实现 SEO 优化：

- `src/entry-server.tsx` — 使用 `renderToString` 在服务端渲染每个路由
- `scripts/prerender.mjs` — 构建后遍历 `sidebar.json` 中的所有路由，生成静态 HTML
- 每个页面通过 `document.title` 动态设置 SEO 友好的标题

构建时 `npm run build` 会自动完成预渲染，无需额外配置。
