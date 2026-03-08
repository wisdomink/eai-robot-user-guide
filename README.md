# EAI Robot User Manual (H5)

FF Master Ultra Edition 产品用户手册，基于 React + Markdown 驱动的静态文档站，支持 SSG 预渲染与 AI 智能问答。

## 功能一览

| 功能 | 说明 |
|------|------|
| AI 智能问答 | 基于 RAG + OpenAI Agents SDK 的对话式问答，自动检索手册内容并生成带引用跳转的回答 |
| AI 语义搜索 | 基于 OpenAI Vector Store Search API 的跨页面语义搜索，支持中英文混合查询 |
| SPA 内部链接 | Markdown 中写路由路径，自动 SPA 导航 |
| 响应式布局 | Desktop 侧边栏常驻，Mobile 抽屉式菜单 |
| 打印友好 | `@media print` 优化，链接自动显示 URL |
| Markdown 驱动 | 内容与代码完全分离，非技术人员可编辑 |
| SSG 预渲染 | 构建时为每个路由生成静态 HTML，支持 SEO |
| 源文档转换 | PDF + Word → Markdown 自动化管道 |

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
| @openai/chatkit-react | — | AI 对话面板（ChatKit 协议） |

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | — | Web 框架 + SSE 流式响应 |
| OpenAI Agents SDK | 0.10+ | Agent 定义 + FileSearchTool |
| OpenAI ChatKit (Python) | 1.6+ | ChatKit 协议桥接 + ResponseStreamConverter |
| OpenAI Vector Store | — | 托管式文档检索（RAG + 语义搜索） |

后端详细文档见 [`rag_server/README.md`](rag_server/README.md)。

## 文件结构

```
eai-robot-user-guide/
├── README.md
├── CLAUDE.md                    ← 项目约定 + Figma MCP 集成规则
├── index.html                   ← Vite 入口
├── package.json
├── vite.config.ts
├── client_run.sh                ← 前端一键启动脚本
├── deploy.sh                    ← 测试环境一键部署（前端 + 后端）
│
├── scripts/
│   ├── convert.mjs              ← 源文档 → Markdown 转换脚本
│   └── prerender.mjs            ← SSG 预渲染脚本
│
├── rag_server/                  ← RAG 智能问答后端（独立 Python 服务）
│   ├── app/                     ← FastAPI 应用
│   │   ├── main.py              ← 入口：/chatkit、/search、/health
│   │   └── services/
│   │       └── chatkit_handler.py ← Agent 定义 + ChatKit 桥接
│   ├── create_vector_store.py   ← 创建 Vector Store 并上传文档
│   ├── server_run.sh            ← 一键启动脚本
│   └── README.md                ← 详细文档
│
├── public/
│   └── images/                  ← 静态图片资源
│
└── src/
    ├── main.tsx                 ← 客户端入口
    ├── entry-server.tsx         ← SSG 服务端入口（renderToString）
    ├── App.tsx                  ← 路由配置（从 sidebar-*.json 自动生成）
    ├── index.css                ← Tailwind + .md-body 样式 + 搜索高亮
    │
    ├── content/                 ← 内容管理（核心）
    │   ├── sidebar-*.json       ← 导航树配置（按产品划分）
    │   ├── index.ts             ← 内容注册表（import.meta.glob）
    │   ├── chunks.ts            ← 内容分块（按 ## 标题切分，用于本地搜索）
    │   └── pages/               ← Markdown 页面
    │
    ├── components/
    │   ├── layout/              ← Header、Sidebar、ContentLayout、MobileMenuDrawer
    │   ├── chat/
    │   │   └── ChatPanel.tsx    ← ChatKit 对话面板（连接 RAG Server）
    │   ├── markdown/
    │   │   └── MarkdownRenderer.tsx
    │   └── search/              ← SearchBar、SearchDropdown、SearchInfoBar
    │
    ├── pages/
    │   └── MarkdownPage.tsx     ← 通用 Markdown 页面
    │
    └── hooks/
        ├── useSearch.ts         ← 搜索逻辑（精确 + 语义合并）
        ├── useSemanticSearch.ts ← 语义搜索 Hook
        ├── useMediaQuery.ts     ← 响应式断点
        └── useSidebarState.ts   ← 侧边栏开关状态
```

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器（https://localhost:5173）
npm run dev
```

> 如需 AI 对话功能，还需启动 RAG Server，详见下方 [AI 智能问答](#ai-智能问答rag-server) 章节。

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

在 `.env` 或部署平台中配置：

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `VITE_CHATKIT_API_URL` | | `http://localhost:8000/chatkit` | RAG Server ChatKit 端点 |
| `VITE_CHATKIT_DOMAIN_KEY` | | `local-dev` | ChatKit 域名标识 |

### 后端（RAG Server）

详见 [`rag_server/README.md` — 环境变量](rag_server/README.md#环境变量)。

## AI 智能问答（RAG Server）

项目内置了基于 RAG 的 AI 对话功能，用户可在页面右侧打开 ChatPanel 向 AI 提问，AI 会自动检索手册内容并生成带引用链接的回答。

### 架构

```
前端 ChatPanel（@openai/chatkit-react）
  │
  │  ChatKit 协议（SSE 流式）
  ▼
RAG Server（FastAPI + OpenAI Agents SDK）
  │
  ├─ FileSearchTool → OpenAI Vector Store 文档检索
  └─ gpt-5 生成回答 → FFRobotConverter 映射引用 → 流式返回
       │
       └─ file_citation → EntitySource(slug) → 前端 entities.onClick → SPA 导航
```

### 本地启动

**方式一：分别启动前端和后端**

```bash
# 终端 1：启动后端
cd rag_server
./server_run.sh

# 终端 2：启动前端
./client_run.sh
```

**方式二：一键部署前端 + 后端**

```bash
./deploy.sh           # 启动所有服务
./deploy.sh status    # 查看状态
./deploy.sh stop      # 停止服务
./deploy.sh restart   # 重启服务
```

启动后 ChatKit 端点为 `http://localhost:8000/chatkit`，前端默认连接此地址。

完整配置说明请参阅 **[`rag_server/README.md`](rag_server/README.md)**。

## 内容管理

### 修改页面内容

直接编辑 `src/content/pages/` 下对应的 `.md` 文件即可。

### 新增页面

**第 1 步** — 创建 Markdown 文件 `src/content/pages/new-topic.md`

**第 2 步** — 在对应产品的 `src/content/sidebar-{product}.json` 中添加条目：

```json
{
  "title": "New Topic",
  "slug": "/new-topic",
  "file": "new-topic.md"
}
```

路由会自动生成，无需修改 `App.tsx`。

### 页面间跳转链接

```markdown
See also: [Safety Guidelines](/safety-guidelines)
```

以 `/` 开头的内部链接会自动通过 React Router 进行 SPA 导航。

### 添加图片

将图片放入 `public/images/`，在 Markdown 中引用：

```markdown
![Alt text](/images/your-image.png)
```

## 内容转换管道

项目使用混合策略从源文档生成 Markdown：**PDF 提取文本**（`pdftotext -layout`），**Word 提取图片**（`mammoth`），合并为带图片引用的 Markdown 文件。

```bash
npm run convert              # 完整管道：文本 + 图片提取 → 合并
npm run convert:text         # 仅提取文本
npm run convert:images       # 仅提取图片
```

## 设计系统

基于 Figma 设计稿提取的 Design Tokens：

- **字体**: Roboto（正文）、Rubik（标题/UI）
- **主色**: Navy `#171A20`、iOS Blue `#0A84FF`、Purple `#6965E0`
- **字号**: h1 36px、h2 30px、h3 17px、body 15px
- **断点**: Desktop ≥1024px、Tablet 768–1023px、Mobile <768px

## SEO

项目通过 SSG（Static Site Generation）预渲染实现 SEO 优化：

- `src/entry-server.tsx` — 使用 `renderToString` 在服务端渲染每个路由
- `scripts/prerender.mjs` — 构建后遍历 `sidebar-master-ultra.json` 中的所有路由，生成静态 HTML
- 每个页面通过 `document.title` 动态设置 SEO 友好的标题

构建时 `npm run build` 会自动完成预渲染，无需额外配置。
