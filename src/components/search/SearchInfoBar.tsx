import { useEffect } from 'react'
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom'
import { useHighlightNavigation } from '@/hooks/useSearch'

export default function SearchInfoBar() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const location = useLocation()
  const highlightTerm = searchParams.get('q') || ''

  const { currentIndex, totalCount, refreshMarks, navigateMatch } = useHighlightNavigation()

  // Refresh marks whenever the highlight term or page changes
  useEffect(() => {
    if (highlightTerm) {
      // Small delay to ensure DOM is rendered with highlights
      const timer = setTimeout(refreshMarks, 100)
      return () => clearTimeout(timer)
    }
  }, [highlightTerm, location.pathname, refreshMarks])

  const handleClear = () => {
    navigate(location.pathname, { replace: true })
  }

  if (!highlightTerm) return null

  return (
    <div className="sticky top-16 z-10 flex items-center gap-3 px-4 md:px-12 py-2.5 bg-purple/8 border-b border-gray-200 text-sm">
      <svg className="w-3.5 h-3.5 text-purple flex-shrink-0" fill="none" viewBox="0 0 16 16">
        <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
        <path d="M11 11L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>

      <span className="text-purple">
        Results for <strong>"{highlightTerm}"</strong>
      </span>

      {totalCount > 0 && (
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
