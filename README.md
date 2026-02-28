# EAI Robot User Manual (H5)

FF Master Ultra Edition 产品用户手册，基于 React + Markdown 驱动的静态文档站，支持 SSG 预渲染与 AI 智能问答。

## 功能一览

| 功能 | 说明 |
|------|------|
| 🤖 AI 智能问答 | 基于 RAG + OpenAI Agent 的对话式问答，自动检索手册内容并生成带引用的回答 |
| 🔍 AI 语义搜索 | 基于 OpenAI Embedding 的跨页面语义搜索，支持中英文混合查询 |
| 🔗 SPA 内部链接 | Markdown 中写路由路径，自动 SPA 导航 |
| 📱 响应式布局 | Desktop 侧边栏常驻，Mobile 抽屉式菜单 |
| 🖨️ 打印友好 | `@media print` 优化，链接自动显示 URL |
| 📝 Markdown 驱动 | 内容与代码完全分离，非技术人员可编辑 |
| ⚡ SSG 预渲染 | 构建时为每个路由生成静态 HTML，支持 SEO |
| 🔄 源文档转换 | PDF + Word → Markdown 自动化管道 |

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19 | UI 框架 |
| Vite | 7 | 构建工具 + 开发服务器 |
| TypeScript | 5.9 | 类型安全 |
| Tailwind CSS | 4 | 样式系统 |
| React Router | 7 | 客户端路由（SPA） |
| marked | 17 | Markdown → HTML 渲染 |
| @openai/chatkit-react | — | AI 对话面板（ChatKit 协议） |
| OpenAI Embedding API | text-embedding-3-small | AI 语义搜索（向量化） |

后端（RAG Server）技术栈详见 [`rag_server/README.md`](rag_server/README.md)。

## 文件结构

```
eai-robot-user-guide/
├── CLAUDE.md                    ← 项目约定 + Figma MCP 集成规则
├── README.md
├── index.html                   ← Vite 入口
├── package.json
├── vite.config.ts
├── tsconfig.app.json
│
├── scripts/
│   ├── convert.mjs              ← 源文档 → Markdown 转换脚本
│   ├── prerender.mjs            ← SSG 预渲染脚本
│   ├── generate-embeddings.mjs  ← 语义搜索向量生成脚本
│   └── dev-embed-server.mjs     ← 本地 Embedding 代理服务
│
├── lambda/
│   └── embedding-proxy/
│       └── index.mjs            ← AWS Lambda 代理（OpenAI Embedding API）
│
├── rag_server/                  ← RAG 智能问答后端（独立 Python 服务）
│   ├── app/                     ← FastAPI 应用
│   ├── server_run.sh            ← 一键启动脚本
│   └── README.md                ← 详细文档
│
├── public/
│   ├── search/
│   │   └── embeddings.json      ← 构建时生成的向量索引
│   └── images/
│       ├── home-hero.png        ← 首页封面图
│       └── docx/                ← convert 脚本从 Word 提取的图片
│
└── src/
    ├── main.tsx                 ← 客户端入口
    ├── entry-server.tsx         ← SSG 服务端入口（renderToString）
    ├── App.tsx                  ← 路由配置（从 sidebar.json 自动生成）
    ├── index.css                ← Tailwind + .md-body 样式 + 搜索高亮
    │
    ├── content/                 ← 📝 内容管理（核心）
    │   ├── sidebar.json         ← 导航树配置（5 个章节）
    │   ├── index.ts             ← 内容注册表（import.meta.glob）
    │   ├── chunks.ts            ← 内容分块（按 ## 标题切分，用于语义搜索）
    │   ├── source/              ← 原始文档（转换输入）
    │   │   ├── manual.pdf       ← 文本提取源
    │   │   └── manual.docx      ← 图片提取源
    │   └── pages/               ← Markdown 页面（25 个）
    │
    ├── components/
    │   ├── layout/              ← 布局组件
    │   │   ├── Header.tsx
    │   │   ├── Sidebar.tsx
    │   │   ├── SidebarNavItem.tsx
    │   │   ├── ContentLayout.tsx
    │   │   └── MobileMenuDrawer.tsx
    │   ├── chat/                ← AI 对话
    │   │   └── ChatPanel.tsx    ← ChatKit 对话面板（连接 RAG Server）
    │   ├── markdown/            ← Markdown 渲染
    │   │   └── MarkdownRenderer.tsx
    │   └── search/              ← 搜索组件
    │       ├── SearchBar.tsx
    │       ├── SearchDropdown.tsx
    │       └── SearchInfoBar.tsx
    │
    ├── pages/
    │   └── MarkdownPage.tsx     ← 通用 Markdown 页面
    │
    ├── hooks/
    │   ├── useSearch.ts         ← 搜索逻辑 + 高亮导航
    │   ├── useSemanticSearch.ts ← AI 语义搜索 Hook
    │   ├── useMediaQuery.ts     ← 响应式断点
    │   └── useSidebarState.ts   ← 侧边栏开关状态
    │
    ├── lib/
    │   └── cosine-similarity.ts ← 向量余弦相似度计算
    │
    └── assets/
        └── icons/               ← SVG 图标
```

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器（http://localhost:5173）
npm run dev
```

> **可选**：如需 AI 对话功能，还需启动 RAG Server，详见下方 [AI 智能问答](#ai-智能问答rag-server) 章节。

### 生产构建

```bash
# 完整构建（含 SSG 预渲染）
npm run build

# 预览构建结果
npm run preview
```

`npm run build` 依次执行：

1. **TypeScript 类型检查** — `tsc -b`
2. **客户端构建** — `vite build`（输出到 `dist/client/`）
3. **服务端构建** — `vite build --ssr`（输出到 `dist/server/`）
4. **SSG 预渲染** — `node scripts/prerender.mjs`（为每个路由生成静态 HTML）

### 语义搜索构建

如需部署语义搜索功能，构建前需额外生成向量索引：

```bash
# 第 1 步：生成语义搜索向量索引（需要 OpenAI API Key）
OPENAI_API_KEY=sk-... npm run generate:embeddings

# 第 2 步：构建（将 embeddings.json 打包进 dist，VITE_EMBEDDING_API_URL 编译进 JS）
VITE_EMBEDDING_API_URL=https://your-api-gateway-url/api/embed npm run build
```

> `generate:embeddings` 独立于 `build`，仅在 Markdown 内容变更时需要重新运行。费用约 $0.0003/次（~16K tokens）。

## 环境变量

### 前端（Vite）

在 `.env` 或部署平台中配置：

| 变量 | 必填 | 默认值 | 说明 |
|------|:----:|--------|------|
| `VITE_EMBEDDING_API_URL` | | `/api/embed` | 语义搜索 Embedding API 端点 |
| `VITE_CHATKIT_API_URL` | | `http://localhost:8000/chatkit` | RAG Server ChatKit 端点 |
| `VITE_CHATKIT_DOMAIN_KEY` | | `local-dev` | ChatKit 域名标识 |
| `OPENAI_API_KEY` | | — | 构建时生成向量索引使用（仅在 `generate:embeddings` 时需要） |

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
  ├─ ChromaDB 向量检索 → 匹配相关文档块
  └─ gpt-4o-mini 生成回答 → 流式返回 + 引用来源
```

### 本地启动

```bash
cd rag_server
chmod +x server_run.sh
./server_run.sh
```

启动后 ChatKit 端点为 `http://localhost:8000/chatkit`，前端默认连接此地址。

完整配置说明（环境变量、手动启动、API 接口、数据流程等）请参阅 **[`rag_server/README.md`](rag_server/README.md)**。

## 语义搜索

基于 OpenAI `text-embedding-3-small` 模型的跨页面语义搜索，支持中英文混合查询（如输入"如何充电"可匹配到 "Charging Procedure" 页面）。

### 架构

```
构建时:
  Markdown 内容 → 按 ## 标题分块 → 调用 OpenAI Embedding API
  → 输出 public/search/embeddings.json（向量索引）

运行时:
  用户输入查询 → AWS Lambda 代理 → OpenAI Embedding API → 返回查询向量
  → 浏览器加载 embeddings.json（缓存） → 余弦相似度匹配 → 排序返回结果
```

### 本地开发

本地调试语义搜索需要三步：

```bash
# 1. 生成向量索引（仅内容变更时需要）
OPENAI_API_KEY=sk-... npm run generate:embeddings

# 2. 启动本地 Embedding 代理（新终端窗口）
OPENAI_API_KEY=sk-... npm run dev:embed
# → Embedding proxy running at http://localhost:3001/api/embed

# 3. 启动 Vite 开发服务器（另一个终端窗口）
npm run dev
# → Vite 自动将 /api/embed 代理到 localhost:3001
```

### 故障排查

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| 搜索无结果 | `embeddings.json` 未生成 | 运行 `npm run generate:embeddings` |
| 502 Embedding service error | 代理未启动或 API Key 无效 | 检查 `npm run dev:embed` 是否正常运行 |
| ECONNREFUSED 3001 | Vite 无法连接代理服务 | 确认代理服务已启动且端口无冲突 |
| 搜索结果不相关 | `embeddings.json` 过期 | 内容更新后重新生成向量索引 |

### AWS Lambda 部署

语义搜索的生产环境使用 AWS Lambda 代理转发 Embedding 请求（隐藏 API Key）。

```bash
# 打包 Lambda 代码
cd lambda/embedding-proxy
zip -r function.zip index.mjs

# 创建 Lambda 函数
aws lambda create-function \
  --function-name eai-manual-embedding-proxy \
  --runtime nodejs20.x \
  --handler index.handler \
  --zip-file fileb://function.zip \
  --role arn:aws:iam::YOUR_ACCOUNT:role/YOUR_LAMBDA_ROLE

# 配置环境变量
aws lambda update-function-configuration \
  --function-name eai-manual-embedding-proxy \
  --environment "Variables={OPENAI_API_KEY=sk-...,ALLOWED_ORIGIN=https://your-domain.com}"
```

然后创建 API Gateway（HTTP API）绑定 `POST /api/embed` 路由到 Lambda，并将 URL 设置为 `VITE_EMBEDDING_API_URL`。

**Lambda 接口**：`POST /api/embed`，body `{ "query": "搜索文本" }`，返回 `{ "embedding": [...] }`（512 维向量）。内置 CORS 限制、500 字符查询长度限制、60 次/分钟/IP 速率限制。

## 内容管理

### 修改页面内容

直接编辑 `src/content/pages/` 下对应的 `.md` 文件即可。

### 新增页面

**第 1 步** — 创建 Markdown 文件 `src/content/pages/new-topic.md`

**第 2 步** — 在 `src/content/sidebar.json` 的对应 section 中添加条目：

```json
{
  "title": "New Topic",
  "slug": "/new-topic",
  "file": "new-topic.md"
}
```

路由会自动生成，无需修改 `App.tsx`。

### 新增章节

在 `sidebar.json` 的 `sections` 数组中添加：

```json
{
  "id": "new-section",
  "title": "New Section",
  "pages": [
    { "title": "Page Title", "slug": "/page-slug", "file": "page-file.md" }
  ]
}
```

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

### 前置依赖

```bash
brew install poppler   # 提供 pdftotext 命令
npm install            # mammoth 等 Node 依赖
```

### 源文件

| 文件 | 用途 |
|------|------|
| `src/content/source/manual.pdf` | 文本提取源 |
| `src/content/source/manual.docx` | 图片提取源 |

### 运行命令

```bash
npm run convert              # 完整管道：文本 + 图片提取 → 合并
npm run convert:text         # 仅提取文本
npm run convert:images       # 仅提取图片
npm run convert -- --chapter 2   # 按章节过滤
```

### 管道流程

1. **图片提取** — 从 Word 按 heading anchor 定位，提取 base64 图片保存到 `public/images/docx/`
2. **文本提取** — 从 PDF 按正则匹配章节边界，转换缩进/列表/表格为 Markdown
3. **合并输出** — 按 `SECTIONS` 配置中的 `images` 规则，将图片引用插入到 Markdown 指定位置

### 添加新章节到转换管道

在 `scripts/convert.mjs` 的 `SECTIONS` 数组中添加配置：

```js
{
  chapter: 3,
  file: 'new-section.md',
  title: 'New Section Title',
  pattern: /^3\.1\s+New Section Title\s*$/m,
  endBefore: /^3\.2\s/m,
  images: [
    { position: 'start', headingId: 'heading_20', name: 'new-image' },
  ],
  tables: [
    { headerPattern: /Header.*Pattern/, hardcoded: '| ... |' },
  ],
}
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
- `scripts/prerender.mjs` — 构建后遍历 `sidebar.json` 中的所有路由，生成静态 HTML
- 每个页面通过 `document.title` 动态设置 SEO 友好的标题

构建时 `npm run build` 会自动完成预渲染，无需额外配置。
