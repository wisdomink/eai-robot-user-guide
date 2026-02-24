import sidebarConfig from './sidebar.json'

// Eagerly import all markdown files at build time
const mdModules = import.meta.glob('./pages/*.md', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

/**
 * Get raw markdown content for a page by filename.
 * @param filename - e.g. "safety-instructions.md"
 */
export function getPageContent(filename: string): string {
  const key = `./pages/${filename}`
  return mdModules[key] ?? ''
}

/**
 * Get all pages with their raw text (markdown stripped) for search indexing.
 */
export function getAllPagesForSearch() {
  return sidebarConfig.sections.flatMap(section =>
    section.pages.map(page => {
      const raw = getPageContent(page.file)
      // Strip markdown syntax for search
      const text = raw
        .replace(/^#{1,6}\s+/gm, '')       // headings
        .replace(/\*\*([^*]+)\*\*/g, '$1')  // bold
        .replace(/\*([^*]+)\*/g, '$1')      // italic
        .replace(/`([^`]+)`/g, '$1')        // inline code
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // links
        .replace(/[>|!\-]/g, '')            // blockquote, table, image, list markers
        .replace(/\s+/g, ' ')
        .trim()
      return {
        title: page.title,
        section: section.title,
        slug: page.slug,
        file: page.file,
        text,
      }
    })
  )
}

export type SidebarConfig = typeof sidebarConfig
export type SectionConfig = SidebarConfig['sections'][number]
export type PageConfig = SectionConfig['pages'][number]

export { sidebarConfig }
