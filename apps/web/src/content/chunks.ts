import allSidebars from './sidebar.json'
import developerSidebars from './developer-sidebar.json'
import { getAimdkRaw } from './aimdk-raw'
import { stripYamlFrontmatter } from './stripYamlFrontmatter'
import { getPageContent, stripMarkdown } from './index'

const AIMDK_PREFIX = 'aimdk/content/'

export interface ContentChunk {
  id: string
  pageSlug: string
  pageTitle: string
  sectionTitle: string
  sectionId: string
  text: string
  textPreview: string
  headingAnchor: string
}

function toAnchor(heading: string): string {
  return heading
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/^-|-$/g, '')
}

/**
 * Split all page content into section-level chunks for semantic search.
 * Each chunk corresponds to a `## ` heading section within a page.
 * Pages without `## ` headings become a single chunk.
 */
function pushChunksFromRaw(
  chunks: ContentChunk[],
  raw: string,
  page: { slug: string; title: string; file: string },
  section: { id: string; title: string }
) {
  const parts = raw.split(/^(?=## )/m)

  for (const part of parts) {
    const headingMatch = part.match(/^## (.+)$/m)
    const sectionTitle = headingMatch ? headingMatch[1].trim() : page.title
    const anchor = headingMatch ? toAnchor(headingMatch[1].trim()) : ''
    const text = stripMarkdown(part)

    if (text.length < 20) continue

    chunks.push({
      id: `${page.file}#${anchor || 'top'}`,
      pageSlug: page.slug,
      pageTitle: page.title,
      sectionTitle,
      sectionId: section.id,
      text,
      textPreview: text.slice(0, 200),
      headingAnchor: anchor,
    })
  }
}

export function getAllChunksForSearch(): ContentChunk[] {
  const chunks: ContentChunk[] = []

  for (const sidebar of Object.values(allSidebars)) {
    for (const section of sidebar.sections) {
      for (const page of section.pages) {
        const raw = getPageContent(page.file)
        if (!raw) continue
        pushChunksFromRaw(chunks, raw, page, section)
      }
    }
  }

  for (const sidebar of Object.values(developerSidebars)) {
    for (const section of sidebar.sections) {
      for (const page of section.pages) {
        const rel = page.file.startsWith(AIMDK_PREFIX)
          ? page.file.slice(AIMDK_PREFIX.length)
          : page.file
        const rawMdx = getAimdkRaw(rel)
        if (!rawMdx) continue
        const raw = stripYamlFrontmatter(rawMdx)
        pushChunksFromRaw(chunks, raw, page, section)
      }
    }
  }

  return chunks
}
