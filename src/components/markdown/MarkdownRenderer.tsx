import { useMemo } from 'react'
import { marked, type Tokens } from 'marked'

// Configure marked
marked.setOptions({ breaks: true, gfm: true })

// Custom renderer for internal links (SPA navigation)
const renderer = new marked.Renderer()
const origLink = renderer.link.bind(renderer)

renderer.link = function (token: Tokens.Link) {
  const { href, title, text } = token
  // Internal links starting with / → use data-spa-link for React Router integration
  if (href && href.startsWith('/') && !href.startsWith('//')) {
    const safeHref = href.replace(/"/g, '&quot;')
    const safeTitle = title ? ` title="${title.replace(/"/g, '&quot;')}"` : ''
    return `<a href="${safeHref}" data-spa-link${safeTitle}>${text}</a>`
  }
  // External links → open in new tab
  const out = origLink(token)
  return out.replace('<a ', '<a target="_blank" rel="noopener" ')
}

marked.use({ renderer })

interface MarkdownRendererProps {
  content: string
  highlightTerm?: string
  className?: string
}

function highlightHTML(html: string, keyword: string): string {
  if (!keyword.trim()) return html
  const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const re = new RegExp(`(${escaped})`, 'gi')
  // Only highlight text outside of HTML tags
  return html.replace(/(<[^>]+>)|([^<]+)/g, (_m, tag: string, text: string) =>
    tag ? tag : text.replace(re, '<mark class="hl">$1</mark>')
  )
}

export default function MarkdownRenderer({ content, highlightTerm, className }: MarkdownRendererProps) {
  const html = useMemo(() => {
    let parsed = marked.parse(content) as string
    if (highlightTerm) {
      parsed = highlightHTML(parsed, highlightTerm)
    }
    return parsed
  }, [content, highlightTerm])

  return (
    <div
      className={`md-body ${className ?? ''}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

export { marked, highlightHTML }
