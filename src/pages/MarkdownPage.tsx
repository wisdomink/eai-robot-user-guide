import { useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import ContentLayout from '@/components/layout/ContentLayout'
import MarkdownRenderer from '@/components/markdown/MarkdownRenderer'
import { getPageContent } from '@/content'

interface MarkdownPageProps {
  file: string
  title: string
}

export default function MarkdownPage({ file, title }: MarkdownPageProps) {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const highlightTerm = searchParams.get('q') || ''

  // Set page title
  useEffect(() => {
    document.title = `${title} - EAI Robot Manual`
  }, [title])

  // Handle SPA link clicks (internal navigation)
  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      const target = (e.target as HTMLElement).closest('a[data-spa-link]') as HTMLAnchorElement | null
      if (target) {
        e.preventDefault()
        const href = target.getAttribute('href')
        if (href) navigate(href)
      }
    },
    [navigate]
  )

  const content = getPageContent(file)
  const isHome = file.endsWith('/home.md')

  return (
    <ContentLayout fullWidth={isHome}>
      {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions */}
      <div onClick={handleClick}>
        <MarkdownRenderer content={content} highlightTerm={highlightTerm} />
      </div>
    </ContentLayout>
  )
}
