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
│   └── prerender.mjs          ← SSG 预渲染脚本
├── public/
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
    │   ├── useMediaQuery.ts   ← 响应式断点
    │   └── useSidebarState.ts ← 侧边栏开关状态
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

`npm run build` 依次执行以下步骤：

1. **TypeScript 类型检查** — `tsc -b`
2. **客户端构建** — `vite build`（输出到 `dist/client/`）
3. **服务端构建** — `vite build --ssr`（输出到 `dist/server/`）
4. **SSG 预渲染** — `node scripts/prerender.mjs`（为每个路由生成静态 HTML）

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
| 🔍 全文搜索 | 跨页面搜索 + 当前页关键词高亮 + ↑↓ 导航 |
| 🔗 SPA 内部链接 | Markdown 中写路由路径，自动 SPA 导航 |
| 📱 响应式布局 | Desktop 侧边栏常驻，Mobile 抽屉式菜单 |
| 🖨️ 打印友好 | `@media print` 优化，链接自动显示 URL |
| 📝 Markdown 驱动 | 内容与代码完全分离，非技术人员可编辑 |
| ⚡ SSG 预渲染 | 构建时为每个路由生成静态 HTML，支持 SEO |
| 🔄 源文档转换 | PDF + Word → Markdown 自动化管道（`npm run convert`） |

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
