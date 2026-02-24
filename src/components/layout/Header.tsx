import { Link } from 'react-router-dom'
import logoDark from '@/assets/icons/logo-dark.svg'
import iconMenu from '@/assets/icons/icon-menu.svg'

interface HeaderProps {
  onMenuToggle: () => void
}

export default function Header({ onMenuToggle }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 flex items-center justify-between h-16 px-4 lg:px-6 bg-navy border-b border-gray-700">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-2 -ml-2 text-white"
          aria-label="Toggle menu"
        >
          <img src={iconMenu} alt="" className="w-6 h-6 invert" />
        </button>
        <Link to="/" className="flex items-center gap-2">
          <img src={logoDark} alt="EAI Robot" className="h-8 w-8" />
          <span className="font-rubik font-semibold text-white text-lg hidden sm:inline">
            User Manual
          </span>
        </Link>
      </div>
    </header>
  )
}
