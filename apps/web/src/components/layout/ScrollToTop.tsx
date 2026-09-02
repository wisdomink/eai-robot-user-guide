import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/** Resets the document position when navigating to a different manual page. */
export default function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])

  return null
}
