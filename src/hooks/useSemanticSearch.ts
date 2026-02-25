import { useState, useRef, useCallback } from 'react'
import { cosineSimilarity } from '@/lib/cosine-similarity'

interface EmbeddingChunk {
  id: string
  pageSlug: string
  pageTitle: string
  sectionTitle: string
  sectionId: string
  headingAnchor: string
  textPreview: string
  embedding: number[]
}

interface EmbeddingsIndex {
  model: string
  dimensions: number
  generatedAt: string
  chunks: EmbeddingChunk[]
}

export interface SemanticResult {
  id: string
  pageSlug: string
  pageTitle: string
  sectionTitle: string
  sectionId: string
  headingAnchor: string
  textPreview: string
  similarity: number
}

const EMBEDDING_API_URL = import.meta.env.VITE_EMBEDDING_API_URL || '/api/embed'
const SIMILARITY_THRESHOLD = 0.3
const MAX_RESULTS = 10

// Module-level cache for embeddings data
let embeddingsCache: EmbeddingsIndex | null = null

async function fetchEmbeddings(): Promise<EmbeddingsIndex> {
  if (embeddingsCache) return embeddingsCache
  const res = await fetch('/search/embeddings.json')
  if (!res.ok) throw new Error(`Failed to load embeddings: ${res.status}`)
  embeddingsCache = await res.json()
  return embeddingsCache!
}

async function fetchQueryEmbedding(query: string): Promise<number[]> {
  const res = await fetch(EMBEDDING_API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Embedding API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return data.embedding
}

export function useSemanticSearch() {
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const searchSemantic = useCallback(async (query: string): Promise<SemanticResult[]> => {
    // Cancel any in-flight request
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    setIsSearching(true)
    setError(null)

    try {
      // Fetch query embedding and cached document embeddings in parallel
      const [queryEmbedding, embeddingsIndex] = await Promise.all([
        fetchQueryEmbedding(query),
        fetchEmbeddings(),
      ])

      // Compute similarity for all chunks
      const scored = embeddingsIndex.chunks.map(chunk => ({
        id: chunk.id,
        pageSlug: chunk.pageSlug,
        pageTitle: chunk.pageTitle,
        sectionTitle: chunk.sectionTitle,
        sectionId: chunk.sectionId,
        headingAnchor: chunk.headingAnchor,
        textPreview: chunk.textPreview,
        similarity: cosineSimilarity(queryEmbedding, chunk.embedding),
      }))

      // Filter by threshold, sort by similarity, take top N
      const results = scored
        .filter(r => r.similarity >= SIMILARITY_THRESHOLD)
        .sort((a, b) => b.similarity - a.similarity)
        .slice(0, MAX_RESULTS)

      setIsSearching(false)
      return results
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        return [] // Cancelled, don't update state
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
