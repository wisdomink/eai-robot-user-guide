# EAI Robot User Manual (H5)

FF Master Ultra Edition 产品用户手册，基于 React + Markdown 驱动的静态文档站，支持 SSG 预渲染。

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 19 | UI 框架 |
| Vite | 7 | 构建工具 + 开发服务器 |
| TypeScript | 5.9 | 类型安全 |
| Tailwind CSS | 4 | 样式系统 |
| React Router | 7 | 客户端路由（SPA） |
| marked | 17 | Markdown → HTML 渲染 |
| OpenAI Embedding API | text-embedding-3-small | AI 语义搜索（向量化） |

## 文件结构

```
h5-test/
├── CLAUDE.md                  ← Figma MCP 集成规则 + 项目约定
├── README.md
├── index.html                 ← Vite 入口
├── package.json
├── vite.config.ts
├── tsconfig.app.json
├── scripts/
│   ├── convert.mjs            ← 源文档 → Markdown 转换脚本
│   ├── prerender.mjs          ← SSG 预渲染脚本
│   └── generate-embeddings.mjs ← 语义搜索向量生成脚本
├── lambda/
│   └── embedding-proxy/
│       └── index.mjs          ← AWS Lambda 代理（OpenAI Embedding API）
├── public/
│   ├── search/
│   │   └── embeddings.json    ← 构建时生成的向量索引（~100KB gzipped）
│   └── images/
│       ├── home-hero.png      ← 首页封面图
│       └── docx/              ← convert 脚本从 Word 提取的图片
└── src/
    ├── main.tsx               ← 客户端入口
    ├── entry-server.tsx       ← SSG 服务端入口（renderToString）
    ├── App.tsx                ← 路由配置（从 sidebar.json 自动生成）
    ├── index.css              ← Tailwind + .md-body 样式 + 搜索高亮
    │
    ├── content/               ← 📝 内容管理（核心）
    │   ├── sidebar.json       ← 导航树配置（5 个章节）
    │   ├── index.ts           ← 内容注册表（import.meta.glob）
    │   ├── chunks.ts          ← 内容分块（按 ## 标题切分，用于语义搜索）
    │   ├── source/            ← 原始文档（转换输入）
    │   │   ├── manual.pdf     ← 文本提取源
    │   │   └── manual.docx    ← 图片提取源
    │   └── pages/             ← Markdown 页面内容（转换输出）
    │       ├── home.md
    │       ├── safety-instructions.md
    │       ├── safety-guidelines.md
    │       ├── maintenance.md
    │       ├── packing-list.md
    │       ├── product-overview.md
    │       ├── computational-unit.md
    │       ├── battery-indicator.md
    │       ├── sensor-fov.md
    │       ├── joint-limits.md
    │       ├── coordinate-systems.md
    │       ├── specifications.md
    │       ├── safety-precautions.md
    │       ├── startup-guide.md
    │       ├── shutdown-guide.md
    │       ├── charging-procedure.md
    │       ├── remote-control.md
    │       ├── robot-interaction.md
    │       ├── ff-robotic-app.md
    │       ├── others.md
    │       ├── locomotion-platform.md
    │       └── contact-information.md
    │
    ├── components/
    │   ├── layout/            ← 布局组件
    │   │   ├── Header.tsx
    │   │   ├── Sidebar.tsx
    │   │   ├── SidebarNavItem.tsx
    │   │   ├── ContentLayout.tsx
    │   │   └── MobileMenuDrawer.tsx
    │   ├── markdown/          ← Markdown 渲染
    │   │   └── MarkdownRenderer.tsx
    │   └── search/            ← 搜索组件
    │       ├── SearchBar.tsx
    │       ├── SearchDropdown.tsx
    │       └── SearchInfoBar.tsx
    │
    ├── pages/
    │   ├── HomePage.tsx       ← 首页（封面布局）
    │   └── MarkdownPage.tsx   ← 通用 Markdown 页面
    │
    ├── hooks/
    │   ├── useSearch.ts       ← 搜索逻辑 + 高亮导航
    │   ├── useSemanticSearch.ts ← AI 语义搜索 Hook（OpenAI + 向量相似度）
    │   ├── useMediaQuery.ts   ← 响应式断点
    │   └── useSidebarState.ts ← 侧边栏开关状态
    │
    ├── lib/
    │   └── cosine-similarity.ts ← 向量余弦相似度计算
    │
    └── assets/
        ├── icons/             ← SVG 图标（React 组件引用）
        └── images/            ← 原始 Figma 导出图片
```

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 生产构建（含 SSG 预渲染）
npm run build

# 预览构建结果
npm run preview
```

### 构建流程

完整的生产部署构建分两步：

```bash
# 第 1 步：生成语义搜索向量索引（需要 OpenAI API Key）
OPENAI_API_KEY=sk-... npm run generate:embeddings

# 第 2 步：构建静态站（将 embeddings.json 打包进 dist）
VITE_EMBEDDING_API_URL=https://your-api-gateway-url/api/embed npm run build
```

其中 `npm run build` 依次执行：

1. **TypeScript 类型检查** — `tsc -b`
2. **客户端构建** — `vite build`（输出到 `dist/client/`，`VITE_EMBEDDING_API_URL` 编译进 JS）
3. **服务端构建** — `vite build --ssr`（输出到 `dist/server/`）
4. **SSG 预渲染** — `node scripts/prerender.mjs`（为每个路由生成静态 HTML）

> **说明**：`generate:embeddings` 独立于 `build`，因为它需要 `OPENAI_API_KEY` 且仅在内容变更时需要重新运行。如果 Markdown 内容未改动，可跳过第 1 步直接 `npm run build`。

## 内容转换管道（convert）

项目使用混合策略从源文档生成 Markdown 页面：**PDF 提取文本**（`pdftotext -layout`），**Word 提取图片**（`mammoth`），最终合并为带图片引用的 Markdown 文件。

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
npm run convert:text         # 仅提取文本（不处理图片）
npm run convert:images       # 仅提取图片（不重新生成文本）
```

支持按章节过滤：

```bash
npm run convert -- --chapter 2          # 仅处理第 2 章
npm run convert:text -- --chapter 1     # 仅处理第 1 章文本
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
  pattern: /^3\.1\s+New Section Title\s*$/m,   // PDF 中的章节起始标记
  endBefore: /^3\.2\s/m,                        // 下一章节的起始标记
  images: [                                      // 可选：图片提取规则
    { position: 'start', headingId: 'heading_20', name: 'new-image' },
  ],
  tables: [                                      // 可选：表格替换规则
    { headerPattern: /Header.*Pattern/, hardcoded: '| ... |' },
  ],
}
```

## 日常维护

### 修改页面内容

直接编辑 `src/content/pages/` 下对应的 `.md` 文件即可，无需修改任何代码。

### 新增页面

**第 1 步** — 创建 Markdown 文件：

```
src/content/pages/new-topic.md
```

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
    {
      "title": "Page Title",
      "slug": "/page-slug",
      "file": "page-file.md"
    }
  ]
}
```

### 页面间跳转链接

在 Markdown 中使用路由路径：

```markdown
See also: [Safety Guidelines](/safety-guidelines)
```

内部链接（以 `/` 开头）会自动通过 React Router 进行 SPA 导航，不会触发页面刷新。

### 添加图片

1. 将图片放入 `public/images/`
2. 在 Markdown 中引用：

```markdown
![Alt text](/images/your-image.png)
```

## 功能一览

| 功能 | 说明 |
|------|------|
| 🔍 AI 语义搜索 | 基于 OpenAI Embedding 的跨页面语义搜索，支持中英文混合查询 |
| 🔗 SPA 内部链接 | Markdown 中写路由路径，自动 SPA 导航 |
| 📱 响应式布局 | Desktop 侧边栏常驻，Mobile 抽屉式菜单 |
| 🖨️ 打印友好 | `@media print` 优化，链接自动显示 URL |
| 📝 Markdown 驱动 | 内容与代码完全分离，非技术人员可编辑 |
| ⚡ SSG 预渲染 | 构建时为每个路由生成静态 HTML，支持 SEO |
| 🔄 源文档转换 | PDF + Word → Markdown 自动化管道（`npm run convert`） |

## 语义搜索配置

项目使用 AI 语义搜索，基于 OpenAI `text-embedding-3-small` 模型实现。搜索支持中英文混合查询（如输入"如何充电"可匹配到 "Charging Procedure" 页面）。

### 架构概览

```
构建时:
  Markdown 内容 → 按 ## 标题分块 → 调用 OpenAI Embedding API
  → 输出 public/search/embeddings.json（向量索引，~100KB gzipped）

运行时:
  用户输入查询 → AWS Lambda 代理 → OpenAI Embedding API → 返回查询向量
  → 浏览器加载 embeddings.json（缓存） → 余弦相似度匹配 → 返回排序结果
```

### 生成向量索引

构建时需要 `OPENAI_API_KEY` 环境变量：

```bash
# 设置 OpenAI API Key
export OPENAI_API_KEY=sk-...

# 生成向量索引
npm run generate:embeddings
```

输出文件 `public/search/embeddings.json`，包含所有内容分块的 512 维向量。每次内容更新后需重新生成。

**费用**：约 $0.0003/次构建（~16K tokens）。

### 前端环境变量

在 `.env` 或部署平台中配置 Lambda 代理端点：

```bash
VITE_EMBEDDING_API_URL=https://your-api-gateway-url/api/embed
```

开发时默认回退到 `/api/embed`，由 Vite proxy 自动转发到本地 embed 服务。

### 本地开发完整启动指南

本地调试语义搜索功能需要三个步骤：**生成向量索引** → **启动 Embedding 代理** → **启动 Vite 开发服务器**。

#### 前置条件

- Node.js 20+
- 有效的 OpenAI API Key（需支持 `text-embedding-3-small` 模型）

#### 第 1 步：生成向量索引（仅内容变更时需要）

首次运行或 Markdown 内容有变更时，需要重新生成 `public/search/embeddings.json`：

```bash
OPENAI_API_KEY=sk-... npm run generate:embeddings
```

成功后会输出生成的 chunk 数量和文件路径。此文件会被 Vite 开发服务器自动提供。

#### 第 2 步：启动本地 Embedding 代理服务

打开一个**新的终端窗口**，进入项目目录，运行：

```bash
OPENAI_API_KEY=sk-... npm run dev:embed
```

启动成功后会看到：

```
  Embedding proxy running at http://localhost:3001/api/embed
```

> **说明**：此服务是对 `lambda/embedding-proxy/index.mjs`（Lambda 函数）的本地包装，监听 3001 端口。可通过 `PORT` 环境变量修改端口。

#### 第 3 步：启动 Vite 开发服务器

打开**另一个终端窗口**，进入项目目录，运行：

```bash
npm run dev
```

Vite 会在 `http://localhost:5173` 启动，并自动将 `/api/embed` 请求代理到 `localhost:3001`（已在 `vite.config.ts` 中配置），因此无需设置 `VITE_EMBEDDING_API_URL` 环境变量。

#### 验证搜索功能

1. 在浏览器中打开 `http://localhost:5173`
2. 点击顶部搜索栏，输入关键词（如"如何充电"或"how to turn on"）
3. 等待片刻（首次搜索会加载 embeddings.json），下拉列表应显示语义匹配的结果
4. 点击结果可跳转到对应页面的匹配段落

#### 常见问题

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| 搜索无结果 | `embeddings.json` 未生成 | 执行第 1 步生成向量索引 |
| 502 Embedding service error | Embedding 代理未启动或 API Key 无效 | 检查第 2 步的终端是否正常运行 |
| ECONNREFUSED 3001 | Vite 无法连接代理服务 | 确认第 2 步的终端已启动且端口无冲突 |
| 搜索结果不相关 | `embeddings.json` 过期 | 内容更新后重新执行第 1 步 |

## AWS Lambda 代理部署

Lambda 代理函数位于 `lambda/embedding-proxy/index.mjs`，负责将用户的搜索查询转发到 OpenAI Embedding API（隐藏 API Key）。

### 部署步骤

1. **创建 Lambda 函数**

   ```bash
   # 打包 Lambda 代码
   cd lambda/embedding-proxy
   zip -r function.zip index.mjs

   # 创建函数（Node.js 20.x 运行时）
   aws lambda create-function \
     --function-name eai-manual-embedding-proxy \
     --runtime nodejs20.x \
     --handler index.handler \
     --zip-file fileb://function.zip \
     --role arn:aws:iam::YOUR_ACCOUNT:role/YOUR_LAMBDA_ROLE
   ```

2. **配置环境变量**

   ```bash
   aws lambda update-function-configuration \
     --function-name eai-manual-embedding-proxy \
     --environment "Variables={OPENAI_API_KEY=sk-...,ALLOWED_ORIGIN=https://your-domain.com}"
   ```

3. **创建 API Gateway**

   ```bash
   # 创建 HTTP API
   aws apigatewayv2 create-api \
     --name eai-manual-api \
     --protocol-type HTTP

   # 添加 POST /api/embed 路由 → 绑定 Lambda
   # 配置 CORS: 允许来源为静态站域名
   ```

4. **更新前端配置**

   将 API Gateway 的 URL 设置为 `VITE_EMBEDDING_API_URL` 环境变量。

### Lambda 功能说明

- **接口**: `POST /api/embed`，body: `{ "query": "搜索文本" }`
- **响应**: `{ "embedding": [0.012, -0.034, ...] }`（512 维向量）
- **安全**: CORS 限制、查询长度限制（500 字符）、内置速率限制（60 次/分钟/IP）
- **费用**: Lambda + API Gateway 免费额度覆盖每月 100 万次请求；OpenAI 约 $0.00001/次查询

## 设计系统

基于 Figma 设计稿提取的 Design Tokens：

- **字体**: Roboto（正文）、Rubik（标题/UI）
- **主色**: Navy `#171A20`、iOS Blue `#0A84FF`、Purple `#6965E0`
- **字号**: h1 36px、h2 30px、h3 17px、body 15px
- **断点**: Desktop ≥1024px、Tablet 768–1023px、Mobile <768px

## SEO 说明

项目已实现 SSG（Static Site Generation）预渲染：

- **`src/entry-server.tsx`** — 使用 `react-dom/server` 的 `renderToString` 在服务端渲染每个路由
- **`scripts/prerender.mjs`** — 构建后自动遍历 `sidebar.json` 中的所有路由，生成对应的静态 HTML 文件
- **动态标题** — 每个页面通过 `document.title` 设置 SEO 友好的标题

构建时 `npm run build` 会自动完成预渲染，无需额外配置。
