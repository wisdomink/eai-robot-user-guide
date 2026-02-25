import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { useNavigate, useLocation, useSearchParams } from 'react-router-dom'
import { useSemanticSearch } from './useSemanticSearch'
import type { SemanticResult } from './useSemanticSearch'
import { getAllChunksForSearch, type ContentChunk } from '@/content/chunks'

export interface SearchResult {
  title: string
  section: string
  sectionTitle: string
  slug: string
  snippet: string
  headingAnchor: string
  similarity: number
  matchType: 'exact' | 'semantic'
}

// ─── Exact search (local, instant) ───────────────────────────

let chunksCache: ContentChunk[] | null = null
function getCachedChunks(): ContentChunk[] {
  if (!chunksCache) chunksCache = getAllChunksForSearch()
  return chunksCache
}

function searchExact(query: string): SearchResult[] {
  const q = query.toLowerCase()
  const chunks = getCachedChunks()

  const scored: { chunk: ContentChunk; score: number; snippet: string }[] = []

  for (const chunk of chunks) {
    let score = 0
    let snippet = chunk.textPreview

    // Title exact match → highest priority
    if (chunk.pageTitle.toLowerCase().includes(q)) {
      score += 100
    }

    // Section title match → high priority
    if (chunk.sectionTitle.toLowerCase().includes(q)) {
      score += 50
    }

    // Body text contains query → medium priority
    const bodyLower = chunk.text.toLowerCase()
    const idx = bodyLower.indexOf(q)
    if (idx !== -1) {
      score += 10
      // Extract snippet with context around the match
      const start = Math.max(0, idx - 40)
      const end = Math.min(chunk.text.length, idx + q.length + 120)
      snippet =
        (start > 0 ? '...' : '') +
        chunk.text.slice(start, end).trim() +
        (end < chunk.text.length ? '...' : '')
    }

    if (score > 0) {
      scored.push({ chunk, score, snippet })
    }
  }

  // Sort by score descending
  scored.sort((a, b) => b.score - a.score)

  return scored.slice(0, 10).map(({ chunk, snippet }) => ({
    title: chunk.pageTitle,
    section: chunk.sectionId,
    sectionTitle: chunk.sectionTitle,
    slug: chunk.pageSlug,
    snippet,
    headingAnchor: chunk.headingAnchor,
    similarity: 0,
    matchType: 'exact' as const,
  }))
}

// ─── Semantic → SearchResult adapter ─────────────────────────

function semanticToSearchResult(r: SemanticResult): SearchResult {
  return {
    title: r.pageTitle,
    section: r.sectionId,
    sectionTitle: r.sectionTitle,
    slug: r.pageSlug,
    snippet: r.textPreview,
    headingAnchor: r.headingAnchor,
    similarity: r.similarity,
    matchType: 'semantic',
  }
}

// ─── Main search hook ────────────────────────────────────────

export function useSearch() {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const [query, setQuery] = useState('')
  const [exactResults, setExactResults] = useState<SearchResult[]>([])
  const [semanticResults, setSemanticResults] = useState<SearchResult[]>([])
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const { searchSemantic, isSearching, error, clearError } = useSemanticSearch()

  // The highlight term active on the current page
  const highlightTerm = searchParams.get('q') || ''

  // INSTANT exact search (no debounce)
  useEffect(() => {
    const trimmed = query.trim()
    if (!trimmed) {
      setExactResults([])
      return
    }
    setExactResults(searchExact(trimmed))
  }, [query])

  // DEBOUNCED semantic search (400ms)
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)

    const trimmed = query.trim()
    if (!trimmed) {
      setSemanticResults([])
      return
    }

    debounceRef.current = setTimeout(async () => {
      const results = await searchSemantic(trimmed)
      setSemanticResults(results.map(semanticToSearchResult))
    }, 400)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query, searchSemantic])

  // Merge: exact first → deduplicate → semantic after
  const results = useMemo(() => {
    const exactKeys = new Set(
      exactResults.map((r) => `${r.slug}#${r.headingAnchor}`)
    )
    const dedupedSemantic = semanticResults.filter(
      (r) => !exactKeys.has(`${r.slug}#${r.headingAnchor}`)
    )
    return [...exactResults, ...dedupedSemantic]
  }, [exactResults, semanticResults])

  // Navigate to a search result page with highlight + section anchor
  const navigateToResult = useCallback(
    (
      slug: string,
      keyword: string,
      headingAnchor?: string,
      matchType?: 'exact' | 'semantic'
    ) => {
      setIsDropdownOpen(false)
      const params = new URLSearchParams()
      if (keyword) params.set('q', keyword)
      if (headingAnchor) params.set('section', headingAnchor)
      // For semantic results, also trigger section highlighting on the target page
      if (matchType === 'semantic' && headingAnchor) {
        params.set('highlight-section', headingAnchor)
      }
      const qs = params.toString()
      navigate(`${slug}${qs ? `?${qs}` : ''}`)
    },
    [navigate]
  )

  // Apply in-page search (update current page's q param)
  const applyInPageSearch = useCallback(
    (keyword: string) => {
      if (!keyword.trim()) {
        navigate(location.pathname, { replace: true })
      } else {
        navigate(
          `${location.pathname}?q=${encodeURIComponent(keyword)}`,
          { replace: true }
        )
      }
    },
    [navigate, location.pathname]
  )

  const clearSearch = useCallback(() => {
    setQuery('')
    setExactResults([])
    setSemanticResults([])
    setIsDropdownOpen(false)
    clearError()
    navigate(location.pathname, { replace: true })
  }, [navigate, location.pathname, clearError])

  return {
    query,
    setQuery,
    results,
    isDropdownOpen,
    setIsDropdownOpen,
    isSearching,
    searchError: error,
    highlightTerm,
    navigateToResult,
    applyInPageSearch,
    clearSearch,
  }
}

// ─── In-page highlight navigation ───────────────────────────

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
      marks.forEach((m) => m.classList.remove('current'))
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
