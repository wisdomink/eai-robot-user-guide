import { useState, useRef, useCallback } from 'react'

export interface SemanticResult {
  pageSlug: string
  pageTitle: string
  sectionTitle: string
  sectionId: string
  headingAnchor: string
  textPreview: string
  similarity: number
}

const SEARCH_API_URL = import.meta.env.VITE_SEARCH_API_URL || '/api/search'
const MAX_RESULTS = 10

export function useSemanticSearch() {
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const searchSemantic = useCallback(async (query: string): Promise<SemanticResult[]> => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setIsSearching(true)
    setError(null)

    try {
      const params = new URLSearchParams({ q: query, limit: String(MAX_RESULTS) })
      const res = await fetch(`${SEARCH_API_URL}?${params}`, {
        signal: controller.signal,
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Search API error (${res.status}): ${text}`)
      }

      const data = await res.json()

      if (data.error) {
        throw new Error(data.error)
      }

      setIsSearching(false)
      return data.results as SemanticResult[]
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        return []
      }
      const message = err instanceof Error ? err.message : 'Search failed'
      setError(message)
      setIsSearching(false)
      return []
    }
  }, [])

  const clearError = useCallback(() => setError(null), [])

  return {
    searchSemantic,
    isSearching,
    error,
    clearError,
  }
}
