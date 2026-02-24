import { sidebarConfig } from '@/content'
import SidebarNavItem from './SidebarNavItem'
import SearchBar from '@/components/search/SearchBar'

interface SidebarProps {
  onNavigate?: () => void
}

export default function Sidebar({ onNavigate }: SidebarProps) {
  return (
    <nav className="py-4 px-2 space-y-1" aria-label="Manual navigation">
      <div className="px-2 pb-3">
        <SearchBar />
      </div>
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
