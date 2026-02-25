import { useEffect, useRef } from 'react'
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom'
import { useHighlightNavigation } from '@/hooks/useSearch'

export default function SearchInfoBar() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const location = useLocation()
  const highlightTerm = searchParams.get('q') || ''
  const sectionAnchor = searchParams.get('section') || ''
  const highlightSection = searchParams.get('highlight-section') || ''

  const { currentIndex, totalCount, refreshMarks, navigateMatch } = useHighlightNavigation()

  // Track highlighted elements for cleanup
  const highlightedEls = useRef<HTMLElement[]>([])
  const cleanupTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Scroll to section anchor when navigating from search
  useEffect(() => {
    if (sectionAnchor) {
      const timer = setTimeout(() => {
        const heading = document.getElementById(sectionAnchor)
        if (heading) {
          heading.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 150)
      return () => clearTimeout(timer)
    }
  }, [sectionAnchor, location.pathname])

  // Apply section-level highlight for semantic search results
  useEffect(() => {
    // Clean up any previous highlights
    for (const el of highlightedEls.current) {
      el.classList.remove('semantic-highlight', 'semantic-highlight-heading')
    }
    highlightedEls.current = []
    if (cleanupTimerRef.current) {
      clearTimeout(cleanupTimerRef.current)
      cleanupTimerRef.current = null
    }

    if (!highlightSection) return

    const timer = setTimeout(() => {
      const heading = document.getElementById(highlightSection)
      if (!heading) return

      const tagName = heading.tagName // e.g. 'H2'
      const tracked: HTMLElement[] = []

      // Highlight the heading itself
      heading.classList.add('semantic-highlight-heading')
      tracked.push(heading)

      // Walk sibling nodes until the next same-level (or higher) heading
      let sibling = heading.nextElementSibling as HTMLElement | null
      while (sibling) {
        if (/^H[1-6]$/.test(sibling.tagName) && sibling.tagName <= tagName) {
          break
        }
        sibling.classList.add('semantic-highlight')
        tracked.push(sibling)
        sibling = sibling.nextElementSibling as HTMLElement | null
      }

      highlightedEls.current = tracked

      // Scroll to the highlighted section
      heading.scrollIntoView({ behavior: 'smooth', block: 'start' })

      // Remove highlight classes after animation completes (3s animation + 0.5s buffer)
      cleanupTimerRef.current = setTimeout(() => {
        for (const el of tracked) {
          el.classList.remove('semantic-highlight', 'semantic-highlight-heading')
        }
        highlightedEls.current = []
      }, 3500)
    }, 200)

    return () => clearTimeout(timer)
  }, [highlightSection, location.pathname])

  // Refresh marks whenever the highlight term or page changes
  useEffect(() => {
    if (highlightTerm) {
      const timer = setTimeout(refreshMarks, 100)
      return () => clearTimeout(timer)
    }
  }, [highlightTerm, location.pathname, refreshMarks])

  const handleClear = () => {
    // Also clean up section highlights immediately
    for (const el of highlightedEls.current) {
      el.classList.remove('semantic-highlight', 'semantic-highlight-heading')
    }
    highlightedEls.current = []
    navigate(location.pathname, { replace: true })
  }

  if (!highlightTerm && !sectionAnchor && !highlightSection) return null

  return (
    <div className="sticky top-[var(--header-height)] z-10 flex items-center gap-3 px-4 md:px-12 py-2.5 bg-[#F3F3FB] border-b border-gray-200 text-sm">
      <svg className="w-3.5 h-3.5 text-purple flex-shrink-0" fill="none" viewBox="0 0 16 16">
        <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
        <path d="M11 11L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>

      <span className="text-purple">
        {highlightTerm ? (
          <>Results for <strong>"{highlightTerm}"</strong></>
        ) : highlightSection ? (
          <>AI matched section</>
        ) : (
          <>Navigated to section</>
        )}
      </span>

      {highlightTerm && totalCount > 0 && (
        <>
          <span className="text-xs text-purple/60">
            {currentIndex + 1} / {totalCount}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => navigateMatch(-1)}
              className="w-6 h-6 flex items-center justify-center rounded border border-purple/30 text-purple text-xs hover:bg-purple/10 transition-colors"
            >
              ↑
            </button>
            <button
              onClick={() => navigateMatch(1)}
              className="w-6 h-6 flex items-center justify-center rounded border border-purple/30 text-purple text-xs hover:bg-purple/10 transition-colors"
            >
              ↓
            </button>
          </div>
        </>
      )}

      <button
        onClick={handleClear}
        className="ml-auto text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded transition-colors"
      >
        ✕ Clear
      </button>
    </div>
  )
}
