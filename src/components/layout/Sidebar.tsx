import { Link } from 'react-router-dom'
import { useProduct } from '@/hooks/useProductContext'
import SidebarNavItem from './SidebarNavItem'
import SearchBar from '@/components/search/SearchBar'

interface SidebarProps {
  onNavigate?: () => void
}

export default function Sidebar({ onNavigate }: SidebarProps) {
  const { current } = useProduct()
  const sidebarConfig = current.sidebar

  return (
    <nav className="py-4 px-3 space-y-1" aria-label="Manual navigation">
      {/* Search */}
      <div className="px-1 pb-3">
        <SearchBar />
      </div>

      {/* Clickable title → cover page */}
      <div className="px-3 pb-2">
        <Link
          to={current.homeRoute}
          onClick={onNavigate}
          className="font-roboto font-semibold text-navy text-[var(--fs-sidebar-title)] leading-tight hover:text-ios-blue transition-colors"
        >
          {sidebarConfig.title}
        </Link>
      </div>

      {/* Separator */}
      <div className="border-b border-gray-200 mx-2 mb-1" />

      {/* Navigation sections */}
      {sidebarConfig.sections.map(section => (
        <SidebarNavItem
          key={section.id}
          section={section}
          onNavigate={onNavigate}
        />
      ))}
    </nav>
  )
}
