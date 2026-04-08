import { useEffect, useState } from 'react'

function readMatch(query: string): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia(query).matches
}

export function useMediaQuery(query: string): boolean {
  // Sync read on client so remounted layouts (e.g. route changes) don’t render one frame
  // as “mobile” before useEffect — that caused sidebar margin flash / shrink-grow.
  const [matches, setMatches] = useState(() => readMatch(query))

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const mql = window.matchMedia(query)
    const update = (event?: MediaQueryListEvent) => {
      setMatches(event?.matches ?? mql.matches)
    }

    update()
    mql.addEventListener('change', update)

    return () => mql.removeEventListener('change', update)
  }, [query])

  return matches
}

export function useIsDesktop() {
  return useMediaQuery('(min-width: 1024px)')
}

export function useIsMobile() {
  return useMediaQuery('(max-width: 767px)')
}
