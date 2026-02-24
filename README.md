# EAI Robot User Manual (H5)

FF Master Ultra Edition 产品用户手册，基于 React + Markdown 驱动的静态文档站。

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
├── public/
│   └── images/                ← Markdown 引用的静态图片
│       ├── home-hero.png
│       ├── packing-list-content.png
│       └── product-structure.png
└── src/
    ├── main.tsx               ← 应用入口
    ├── App.tsx                ← 路由配置（从 sidebar.json 自动生成）
    ├── index.css              ← Tailwind + .md-body 样式 + 搜索高亮
    │
    ├── content/               ← 📝 内容管理（核心）
    │   ├── sidebar.json       ← 导航树配置
    │   ├── index.ts           ← 内容注册表（import.meta.glob）
    │   └── pages/             ← Markdown 页面内容
    │       ├── home.md
    │       ├── safety-instructions.md
    │       ├── safety-guidelines.md
    │       ├── maintenance.md
    │       ├── packing-list.md
    │       ├── product-overview.md
    │       ├── product-structure.md
    │       ├── debugging-interface.md
    │       ├── sdk-interface.md
    │       ├── computational-unit.md
    │       └── battery-indicator.md
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

# 生产构建
npm run build

# 预览构建结果
npm run preview
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
| ⚡ 构建时打包 | 所有 .md 通过 `import.meta.glob` 在构建时内联 |

## 设计系统

基于 Figma 设计稿提取的 Design Tokens：

- **字体**: Roboto（正文）、Rubik（标题/UI）
- **主色**: Navy `#171A20`、iOS Blue `#0A84FF`、Purple `#6965E0`
- **字号**: h1 36px、h2 30px、h3 17px、body 15px
- **断点**: Desktop ≥1024px、Tablet 768–1023px、Mobile <768px

## SEO 说明

当前为纯 SPA 架构，所有 Markdown 内容在构建时打包进 JS bundle。如需搜索引擎索引，可选择以下预渲染方案：

- **react-snap** — 零配置，使用 Puppeteer 爬取并生成静态 HTML
- **vite-plugin-prerender** — Vite 插件，构建后自动预渲染指定路由
- **自定义 SSG 脚本** — 使用 `react-dom/server` 的 `renderToString` 为每个路由生成 HTML

每个页面已通过 `document.title` 动态设置标题，为预渲染做好了准备。
