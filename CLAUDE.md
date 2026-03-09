# Project: EAI Robot User Manual (H5)

## Tech Stack
- **Framework**: React 19 + TypeScript
- **Build**: Vite 7
- **Styling**: Tailwind CSS v4 (with `@theme` directive for design tokens)
- **Routing**: React Router DOM v7 (BrowserRouter, client-side SPA)
- **Content**: Markdown files in `src/content/pages/`, rendered via `marked`
- **Search**: Cross-page full-text search + in-page keyword highlighting

## Design Tokens (from Figma)
- **Colors**: Navy `#171A20`, iOS Blue `#0A84FF`, Purple `#6965E0`, Light Purple `#D8D8FF`
- **Fonts**: Roboto (body), Rubik (headings/UI)
- **Font Sizes**: h1=36px, h2=30px, h3=17px, body=15px

## Figma MCP Integration Rules

### Required Workflow
1. Run `get_figma_data` first to fetch the structured representation for the exact node(s).
2. If the response is too large or truncated, request specific child nodes by ID.
3. Use `download_figma_images` to get visual assets (icons, hero images, diagrams).
4. Only begin implementation after gathering both structural data and visual references.
5. Translate Figma output into project conventions (see below).

### Implementation Rules
- Treat Figma MCP output (React + Tailwind) as a **representation of design**, not final code.
- Reuse existing components (`ContentLayout`, `Header`, `Sidebar`, `MarkdownRenderer`) instead of duplicating.
- Apply project color tokens (`navy`, `ios-blue`, `purple`) and typography scale from `@theme` in `index.css`.
- Validate against Figma for 1:1 visual parity.

### Asset Rules
- If the Figma MCP Server returns a localhost source for an image or SVG, use that source directly.
- DO NOT import or add new icon packages (lucide, heroicons, etc.) — use inline SVGs or existing icons in `src/assets/icons/`.
- DO NOT create placeholder images if a real source is available.
- Download images to `public/images/` for use in markdown content, or `src/assets/` for use in React components.

## Project Architecture

### Content Management
- Navigation structure: `src/content/sidebar.json` (all products in one file, keyed by product ID)
- Page content: `src/content/pages/*.md` (Markdown files)
- Content registry: `src/content/index.ts` (imports all .md via `import.meta.glob`)
- To add a new page: (1) create `.md` file, (2) add entry to the corresponding `sidebar-{product}.json`

### Component Structure
```
src/
├── content/           ← Markdown content + config
│   ├── sidebar-*.json ← Navigation tree (per product)
│   ├── index.ts       ← Content registry
│   └── pages/*.md     ← Page content
├── components/
│   ├── layout/        ← Header, Sidebar, ContentLayout, MobileMenuDrawer
│   ├── search/        ← SearchBar, SearchDropdown, SearchInfoBar
│   └── markdown/      ← MarkdownRenderer
├── pages/             ← React page components (HomePage, MarkdownPage)
├── hooks/             ← useSearch, useMediaQuery, useSidebarState
├── assets/            ← Icons (SVG), images used by components
└── types/             ← TypeScript interfaces
```

### Responsive Breakpoints
- Desktop: `>= 1024px` (lg) — sidebar always visible
- Tablet: `768px – 1023px` — sidebar hidden, hamburger menu
- Mobile: `< 768px` — full mobile layout with drawer sidebar

### SEO
- Each route sets `document.title` dynamically
- SSG-ready architecture: `entry-server.tsx` for static HTML generation
- All content is bundled at build time (not fetched at runtime)
