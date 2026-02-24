import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { getAllPagesForSearch } from '@/content'

export interface SearchResult {
  title: string
  section: string
  slug: string
  file: string
  snippet: string
}

function getSnippet(text: string, keyword: string): string {
  const idx = text.toLowerCase().indexOf(keyword.toLowerCase())
  if (idx === -1) return text.slice(0, 140) + (text.length > 140 ? '…' : '')
  const start = Math.max(0, idx - 40)
  const raw = (start > 0 ? '…' : '') + text.slice(start, start + 140) + (start + 140 < text.length ? '…' : '')
  return raw
}

export function useSearch() {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const [query, setQuery] = useState('')
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // The highlight term active on the current page
  const highlightTerm = searchParams.get('q') || ''

  // Build search index (memoized, built once from all page content)
  const searchIndex = useMemo(() => getAllPagesForSearch(), [])

  // Debounced query for search
  const [debouncedQuery, setDebouncedQuery] = useState('')

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setDebouncedQuery(query)
    }, 200)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query])

  // Cross-page search results
  const results: SearchResult[] = useMemo(() => {
    if (!debouncedQuery.trim()) return []
    const kw = debouncedQuery.toLowerCase()
    return searchIndex
      .filter(p => p.text.toLowerCase().includes(kw) || p.title.toLowerCase().includes(kw))
      .map(hit => ({
        ...hit,
        snippet: getSnippet(hit.text, debouncedQuery),
      }))
  }, [debouncedQuery, searchIndex])

  // Navigate to a search result page with highlight
  const navigateToResult = useCallback(
    (slug: string, keyword: string) => {
      setIsDropdownOpen(false)
      navigate(`${slug}?q=${encodeURIComponent(keyword)}`)
    },
    [navigate]
  )

  // Apply in-page search (navigate to current page with q param)
  const applyInPageSearch = useCallback(
    (keyword: string) => {
      if (!keyword.trim()) {
        // Remove q param
        navigate(location.pathname, { replace: true })
      } else {
        navigate(`${location.pathname}?q=${encodeURIComponent(keyword)}`, { replace: true })
      }
    },
    [navigate, location.pathname]
  )

  const clearSearch = useCallback(() => {
    setQuery('')
    setDebouncedQuery('')
    setIsDropdownOpen(false)
    navigate(location.pathname, { replace: true })
  }, [navigate, location.pathname])

  return {
    query,
    setQuery,
    results,
    isDropdownOpen,
    setIsDropdownOpen,
    highlightTerm,
    navigateToResult,
    applyInPageSearch,
    clearSearch,
  }
}

// In-page highlight navigation (for marks rendered in the DOM)
export function useHighlightNavigation() {
  const [currentIndex, setCurrentIndex] = useState(-1)
  const [totalCount, setTotalCount] = useState(0)

  const refreshMarks = useCallback(() => {
    const marks = document.querySelectorAll('mark.hl')
    setTotalCount(marks.length)
    if (marks.length > 0) {
      setCurrentIndex(0)
      marks[0]?.classList.add('current')
      marks[0]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    } else {
      setCurrentIndex(-1)
    }
  }, [])

  const navigateMatch = useCallback(
    (direction: 1 | -1) => {
      const marks = document.querySelectorAll('mark.hl')
      if (marks.length === 0) return
      marks.forEach(m => m.classList.remove('current'))
      const next = (currentIndex + direction + marks.length) % marks.length
      setCurrentIndex(next)
      marks[next]?.classList.add('current')
      marks[next]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    },
    [currentIndex]
  )

  return {
    currentIndex,
    totalCount,
    refreshMarks,
    navigateMatch,
  }
}
