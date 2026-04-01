import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import clsx from 'clsx'
import allSidebars from '@/content/sidebar.json'
import SidebarNavItem from './SidebarNavItem'
import SearchBar from '@/components/search/SearchBar'

const sidebarEntries = Object.entries(allSidebars)

interface SidebarProps {
  onNavigate?: () => void
}

function ProductGroup({
  productId,
  sidebar,
  onNavigate,
}: {
  productId: string
  sidebar: (typeof allSidebars)[keyof typeof allSidebars]
  onNavigate?: () => void
}) {
  const { pathname } = useLocation()
  const productBasePath = `/${productId}`
  const isActive = pathname === productBasePath || pathname.startsWith(`${productBasePath}/`)
  const [isExpanded, setIsExpanded] = useState(isActive)

  useEffect(() => {
    if (isActive) setIsExpanded(true)
  }, [isActive])

  return (
    <div>
      <button
        onClick={() => setIsExpanded(prev => !prev)}
        className="w-full flex items-center gap-1.5 px-3 py-2 text-left font-roboto font-semibold text-navy text-[var(--fs-sidebar-title)] leading-tight hover:text-ios-blue transition-colors cursor-pointer"
      >
        <svg
          className={clsx(
            'w-4 h-4 transition-transform flex-shrink-0',
            isExpanded ? 'rotate-90' : 'rotate-0'
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        <span>{sidebar.title}</span>
      </button>

      {isExpanded && (
        <div className="pl-4">
          {sidebar.sections.map(section => (
            <SidebarNavItem
              key={`${productId}-${section.id}`}
              section={section}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function Sidebar({ onNavigate }: SidebarProps) {
  return (
    <nav className="py-4 px-3 space-y-1" aria-label="Manual navigation">
      <div className="px-1 pb-3">
        <SearchBar />
      </div>

      {sidebarEntries.map(([productId, sidebar], idx) => (
        <div key={productId}>
          {idx > 0 && <div className="border-b border-gray-200 mx-2 mb-1" />}
          <ProductGroup
            productId={productId}
            sidebar={sidebar}
            onNavigate={onNavigate}
          />
        </div>
      ))}
    </nav>
  )
}
