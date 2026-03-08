import sidebarConfig from './sidebar-master-ultra.json'
import futuristSidebarConfig from './sidebar-futurist-ultra.json'
import aegiseduSidebarConfig from './sidebar-aegis-edu.json'
import aegisSidebarConfig from './sidebar-aegis-ultra.json'

// Eagerly import all markdown files at build time
const masterModules = import.meta.glob('./pages/master-ultra/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

const futuristModules = import.meta.glob('./pages/futurist-ultra/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

const aegiseduModules = import.meta.glob('./pages/aegis-edu/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

const aegisModules = import.meta.glob('./pages/aegis-ultra/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

const mdModules: Record<string, string> = { ...masterModules, ...futuristModules, ...aegiseduModules, ...aegisModules }

/**
 * Get raw markdown content for a page by filename.
 * @param filename - e.g. "master-ultra/safety-instructions.md" or "futurist-ultra/foreword.md"
 */
export function getPageContent(filename: string): string {
  const key = `./pages/${filename}`
  return mdModules[key] ?? ''
}

/**
 * Strip markdown syntax from raw text for plain-text indexing.
 */
export function stripMarkdown(raw: string): string {
  return raw
    .replace(/^#{1,6}\s+/gm, '')       // headings
    .replace(/!\[[^\]]*\]\([^)]+\)/g, '') // images
    .replace(/\*\*([^*]+)\*\*/g, '$1')  // bold
    .replace(/\*([^*]+)\*/g, '$1')      // italic
    .replace(/`([^`]+)`/g, '$1')        // inline code
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // links
    .replace(/[>|!\-]/g, '')            // blockquote, table, image, list markers
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * Get all pages with their raw text (markdown stripped) for search indexing.
 * Includes pages from all product sidebars.
 */
export function getAllPagesForSearch() {
  const allSidebars = [sidebarConfig, futuristSidebarConfig, aegiseduSidebarConfig, aegisSidebarConfig]
  return allSidebars.flatMap(sidebar =>
    sidebar.sections.flatMap(section =>
      section.pages.map(page => {
        const raw = getPageContent(page.file)
        const text = stripMarkdown(raw)
        return {
          title: page.title,
          section: section.title,
          slug: page.slug,
          file: page.file,
          text,
        }
      })
    )
  )
}

export type SidebarConfig = typeof sidebarConfig
export type SectionConfig = SidebarConfig['sections'][number]
export type PageConfig = SectionConfig['pages'][number]

export { sidebarConfig, futuristSidebarConfig, aegiseduSidebarConfig, aegisSidebarConfig }
