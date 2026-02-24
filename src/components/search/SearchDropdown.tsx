import { useEffect, useRef } from 'react'
import type { SearchResult } from '@/hooks/useSearch'

interface SearchDropdownProps {
  results: SearchResult[]
  query: string
  onSelect: (slug: string) => void
  onClose: () => void
}

function escapeHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function highlightSnippet(text: string, keyword: string): string {
  if (!keyword.trim()) return escapeHtml(text)
  const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const htmlEscapedKeyword = escaped.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return escapeHtml(text).replace(
    new RegExp(`(${htmlEscapedKeyword})`, 'gi'),
    '<mark class="bg-yellow-200 text-navy rounded px-0.5">$1</mark>'
  )
}

export default function SearchDropdown({ results, query, onSelect, onClose }: SearchDropdownProps) {
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close on click outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        // Check if clicked on search input (parent)
        const searchWrap = dropdownRef.current.closest('.relative')
        if (searchWrap && searchWrap.contains(e.target as Node)) return
        onClose()
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  if (!query.trim()) return null

  return (
    <div
      ref={dropdownRef}
      className="absolute top-[calc(100%+4px)] left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg z-[400] max-h-80 overflow-y-auto"
    >
      {results.length === 0 ? (
        <div className="px-4 py-5 text-center text-gray-400 text-sm">
          No results for "<strong className="text-gray-600">{query}</strong>"
        </div>
      ) : (
        results.map((result, idx) => (
          <button
            key={`${result.slug}-${idx}`}
            onClick={() => onSelect(result.slug)}
            className="w-full text-left px-4 py-3 border-b border-gray-50 last:border-b-0 hover:bg-purple/5 transition-colors"
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold text-purple">{result.title}</span>
              <span className="text-[10px] text-gray-400">{result.section}</span>
            </div>
            <div
              className="text-xs text-gray-500 leading-relaxed line-clamp-2"
              dangerouslySetInnerHTML={{ __html: highlightSnippet(result.snippet, query) }}
            />
          </button>
        ))
      )}
    </div>
  )
}
