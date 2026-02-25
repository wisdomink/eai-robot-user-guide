import { useEffect, useRef } from 'react'
import type { SearchResult } from '@/hooks/useSearch'

interface SearchDropdownProps {
  results: SearchResult[]
  query: string
  isSearching: boolean
  searchError: string | null
  onSelect: (slug: string, headingAnchor: string, matchType: 'exact' | 'semantic') => void
  onClose: () => void
}

function escapeHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function highlightSnippet(text: string, keyword: string): string {
  if (!keyword.trim()) return escapeHtml(text)
  // Try to highlight individual words from the query
  const words = keyword.trim().split(/\s+/).filter(w => w.length >= 2)
  if (words.length === 0) return escapeHtml(text)
  const escaped = words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')
  return escapeHtml(text).replace(
    new RegExp(`(${escaped})`, 'gi'),
    '<mark class="bg-yellow-200 text-navy rounded px-0.5">$1</mark>'
  )
}

function formatSimilarity(similarity: number): string {
  return `${Math.round(similarity * 100)}%`
}

// ─── Single result item ──────────────────────────────────────

function ResultItem({
  result,
  query,
  onSelect,
}: {
  result: SearchResult
  query: string
  onSelect: (slug: string, headingAnchor: string, matchType: 'exact' | 'semantic') => void
}) {
  return (
    <button
      onClick={() => onSelect(result.slug, result.headingAnchor, result.matchType)}
      className="w-full text-left px-4 py-3 border-b border-gray-50 last:border-b-0 hover:bg-purple/5 transition-colors"
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-bold text-purple">{result.title}</span>
        {result.sectionTitle !== result.title && (
          <span className="text-[10px] text-gray-400">› {result.sectionTitle}</span>
        )}
        {result.matchType === 'semantic' && (
          <span className="ml-auto text-[10px] text-purple/40 font-mono">
            {formatSimilarity(result.similarity)}
          </span>
        )}
        {result.matchType === 'exact' && (
          <span className="ml-auto text-[10px] text-ios-blue/50 font-mono">exact</span>
        )}
      </div>
      <div
        className="text-xs text-gray-500 leading-relaxed line-clamp-2"
        dangerouslySetInnerHTML={{ __html: highlightSnippet(result.snippet, query) }}
      />
    </button>
  )
}

// ─── Dropdown component ──────────────────────────────────────

export default function SearchDropdown({ results, query, isSearching, searchError, onSelect, onClose }: SearchDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        const searchWrap = dropdownRef.current.closest('.relative')
        if (searchWrap && searchWrap.contains(e.target as Node)) return
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  if (!query.trim()) return null

  const exactGroup = results.filter(r => r.matchType === 'exact')
  const semanticGroup = results.filter(r => r.matchType === 'semantic')

  return (
    <div
      ref={dropdownRef}
      className="absolute top-[calc(100%+4px)] left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg z-[400] max-h-80 overflow-y-auto"
    >
      {/* Full loading state (no results at all yet) */}
      {isSearching && results.length === 0 && (
        <div className="px-4 py-5 text-center text-gray-400 text-sm">
          <svg className="w-4 h-4 mx-auto mb-2 animate-spin text-purple" fill="none" viewBox="0 0 16 16">
            <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" strokeDasharray="28" strokeDashoffset="8" strokeLinecap="round" />
          </svg>
          Searching...
        </div>
      )}

      {/* Error state */}
      {searchError && (
        <div className="px-4 py-4 text-center text-sm">
          <div className="text-red-500 mb-1">Search unavailable</div>
          <div className="text-gray-400 text-xs">{searchError}</div>
        </div>
      )}

      {/* No results */}
      {!isSearching && !searchError && results.length === 0 && (
        <div className="px-4 py-5 text-center text-gray-400 text-sm">
          No results for "<strong className="text-gray-600">{query}</strong>"
        </div>
      )}

      {/* ── Exact matches group ── */}
      {exactGroup.length > 0 && (
        <>
          <div className="px-4 py-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider bg-gray-50 border-b border-gray-100 sticky top-0 z-10">
            精确匹配
          </div>
          {exactGroup.map((result, idx) => (
            <ResultItem
              key={`exact-${result.slug}-${result.headingAnchor}-${idx}`}
              result={result}
              query={query}
              onSelect={onSelect}
            />
          ))}
        </>
      )}

      {/* ── Semantic matches group ── */}
      {semanticGroup.length > 0 && (
        <>
          <div className="px-4 py-1.5 text-[10px] font-semibold text-purple/60 uppercase tracking-wider bg-purple/4 border-b border-gray-100 sticky top-0 z-10">
            <span className="inline-flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" viewBox="0 0 16 16">
                <path d="M8 1L10 5.5L15 6.5L11.5 10L12.5 15L8 12.5L3.5 15L4.5 10L1 6.5L6 5.5L8 1Z" fill="currentColor" opacity="0.5"/>
              </svg>
              AI 语义匹配
            </span>
          </div>
          {semanticGroup.map((result, idx) => (
            <ResultItem
              key={`semantic-${result.slug}-${result.headingAnchor}-${idx}`}
              result={result}
              query={query}
              onSelect={onSelect}
            />
          ))}
        </>
      )}

      {/* Inline loading: exact results shown, semantic still loading */}
      {isSearching && exactGroup.length > 0 && semanticGroup.length === 0 && (
        <div className="px-4 py-3 text-center text-gray-400 text-xs flex items-center justify-center gap-2">
          <svg className="w-3 h-3 animate-spin text-purple/50" fill="none" viewBox="0 0 16 16">
            <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" strokeDasharray="28" strokeDashoffset="8" strokeLinecap="round" />
          </svg>
          AI searching...
        </div>
      )}
    </div>
  )
}
