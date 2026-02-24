import { Link } from 'react-router-dom'
import logoDark from '@/assets/icons/logo-dark.svg'

interface HeaderProps {
  onMenuToggle: () => void
}

export default function Header({ onMenuToggle }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 flex items-center justify-between h-14 px-4 bg-white border-b border-gray-200">
      {/* Left: Hamburger menu toggle (always visible) */}
      <button
        onClick={onMenuToggle}
        className="p-2 -ml-2 text-navy hover:bg-gray-100 rounded-md transition-colors"
        aria-label="Toggle sidebar"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      {/* Right: Company Logo */}
      <Link to="/" className="p-1">
        <img src={logoDark} alt="EAI Robot" className="h-8 w-8" />
      </Link>
    </header>
  )
}
