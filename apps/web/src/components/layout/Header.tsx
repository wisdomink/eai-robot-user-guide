import logoDark from '@/assets/icons/logo-dark.svg'

interface HeaderProps {
  onMenuToggle: () => void
}

export default function Header({ onMenuToggle }: HeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between h-[var(--header-height)] px-[clamp(12px,1.2vw,24px)] bg-white border-b border-gray-200">
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

      <div className="flex items-center">
        <a href="https://www.ff.com/" className="p-[clamp(2px,0.3vw,6px)]">
          <img
            src={logoDark}
            alt="EAI Robot"
            className="h-[var(--icon-md)] w-[var(--icon-md)]"
          />
        </a>
      </div>
    </header>
  )
}
