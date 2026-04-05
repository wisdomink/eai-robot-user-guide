import { useEffect, useState } from 'react'

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false)

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
