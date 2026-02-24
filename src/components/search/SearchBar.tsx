import { useRef, useCallback } from 'react'
import { useSearch } from '@/hooks/useSearch'
import SearchDropdown from './SearchDropdown'

export default function SearchBar() {
  const {
    query,
    setQuery,
    results,
    isDropdownOpen,
    setIsDropdownOpen,
    navigateToResult,
    applyInPageSearch,
    clearSearch,
  } = useSearch()
  const inputRef = useRef<HTMLInputElement>(null)
  const wrapRef = useRef<HTMLDivElement>(null)

  const handleInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = e.target.value
      setQuery(val)
      setIsDropdownOpen(!!val.trim())
      // Also apply in-page highlight on the current page
      if (val.trim()) {
        applyInPageSearch(val.trim())
      } else {
        applyInPageSearch('')
      }
    },
    [setQuery, setIsDropdownOpen, applyInPageSearch]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        clearSearch()
        inputRef.current?.blur()
      }
      if (e.key === 'Enter' && results.length > 0) {
        e.preventDefault()
        navigateToResult(results[0].slug, query)
      }
    },
    [clearSearch, results, navigateToResult, query]
  )

  const handleFocus = useCallback(() => {
    if (query.trim()) setIsDropdownOpen(true)
  }, [query, setIsDropdownOpen])

  // Close dropdown when clicking outside
  const handleResultClick = useCallback(
    (slug: string) => {
      navigateToResult(slug, query)
    },
    [navigateToResult, query]
  )

  return (
    <div ref={wrapRef} className="relative">
      <div className="flex items-center gap-2 px-3 py-2 border border-gray-200 bg-gray-50 focus-within:border-purple focus-within:ring-2 focus-within:ring-purple/15 focus-within:bg-white transition-all">
        <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 16 16">
          <circle cx="7" cy="7" r="5" stroke="currentColor" strokeWidth="1.5" />
          <path d="M11 11L14 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          placeholder="Search..."
          className="bg-transparent text-sm text-navy outline-none w-full placeholder-gray-400 font-roboto"
          autoComplete="off"
          spellCheck={false}
        />
        {query && (
          <button
            onClick={clearSearch}
            className="text-gray-400 hover:text-gray-600 text-xs p-0.5 rounded transition-colors"
          >
            ✕
          </button>
        )}
      </div>

      {isDropdownOpen && (
        <SearchDropdown
          results={results}
          query={query}
          onSelect={handleResultClick}
          onClose={() => setIsDropdownOpen(false)}
        />
      )}
    </div>
  )
}
