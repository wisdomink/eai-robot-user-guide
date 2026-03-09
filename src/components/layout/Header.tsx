import { Link } from 'react-router-dom'
import logoDark from '@/assets/icons/logo-dark.svg'

interface HeaderProps {
  onMenuToggle: () => void
}

export default function Header({ onMenuToggle }: HeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between h-[var(--header-height)] px-[clamp(12px,1.2vw,24px)] bg-white border-b border-gray-200">
      {/* Left: Hamburger */}
      <div className="flex items-center">
        <button
          onClick={onMenuToggle}
          className="p-[clamp(4px,0.5vw,10px)] text-navy hover:bg-gray-100 rounded-md transition-colors"
          aria-label="Toggle sidebar"
        >
          <svg
            className="w-[var(--icon-sm)] h-[var(--icon-sm)]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
      </div>

      {/* Right: Chat + Company Logo */}
      <div className="flex items-center gap-2">
        <button className="chat-btn" id="chatToggleBtn" title="Ask AI">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M14 1H2a1 1 0 00-1 1v8a1 1 0 001 1h2v3l3-3h7a1 1 0 001-1V2a1 1 0 00-1-1z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"/>
            <circle cx="5" cy="6" r="0.8" fill="currentColor"/>
            <circle cx="8" cy="6" r="0.8" fill="currentColor"/>
            <circle cx="11" cy="6" r="0.8" fill="currentColor"/>
          </svg>
          Ask AI
          <span className="chat-btn-dot" id="chatBtnDot"></span>
        </button>
        <Link to="/" className="p-[clamp(2px,0.3vw,6px)]">
          <img
            src={logoDark}
            alt="EAI Robot"
            className="h-[var(--icon-md)] w-[var(--icon-md)]"
          />
        </Link>
      </div>
    </header>
  )
}
