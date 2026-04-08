import { Link, useLocation } from 'react-router-dom'
import clsx from 'clsx'
import logoDark from '@/assets/icons/logo-dark.svg'

interface HeaderProps {
  onMenuToggle: () => void
}

export default function Header({ onMenuToggle }: HeaderProps) {
  const { pathname } = useLocation()
  const isDeveloper = pathname.startsWith('/developer')

  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between h-[var(--header-height)] px-[clamp(12px,1.2vw,24px)] bg-white border-b border-gray-200">
      <div className="flex items-center gap-2">
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
        <nav className="hidden sm:flex items-center gap-1 text-[clamp(11px,1vw,13px)] font-roboto">
          <Link
            to="/futurist"
            className={clsx(
              'px-2 py-1 rounded-md font-medium transition-colors',
              !isDeveloper ? 'bg-purple/10 text-purple' : 'text-navy hover:bg-gray-100'
            )}
          >
            Product manuals
          </Link>
          <span className="text-gray-300 select-none" aria-hidden>
            |
          </span>
          <Link
            to="/developer/en"
            className={clsx(
              'px-2 py-1 rounded-md font-medium transition-colors',
              isDeveloper ? 'bg-purple/10 text-purple' : 'text-navy hover:bg-gray-100'
            )}
          >
            Developer docs
          </Link>
        </nav>
      </div>

      <div className="flex items-center gap-2">
        <Link
          to="/admin"
          className="chat-btn"
          title="管理后台"
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M13.5 8.5a5.5 5.5 0 0 1-11 0" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
            <path d="M8 1v3M3.5 2.5l1.5 2.5M12.5 2.5l-1.5 2.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
            <circle cx="8" cy="8.5" r="1.2" fill="currentColor" />
          </svg>
          管理后台
        </Link>
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
