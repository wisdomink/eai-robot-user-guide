import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import clsx from 'clsx'
import type { SectionConfig } from '@/content'

interface SidebarNavItemProps {
  section: SectionConfig
  onNavigate?: () => void
}

export default function SidebarNavItem({ section, onNavigate }: SidebarNavItemProps) {
  const location = useLocation()

  const isChildActive = section.pages.some(page => page.slug === location.pathname)
  const [isExpanded, setIsExpanded] = useState(isChildActive)

  const hasPages = section.pages.length > 0

  return (
    <div>
      <button
        onClick={() => hasPages && setIsExpanded(!isExpanded)}
        className={clsx(
          'w-full flex items-center justify-between py-2 px-3 text-left text-sm font-rubik rounded-md transition-colors',
          'font-semibold text-navy',
          hasPages ? 'hover:bg-gray-100 cursor-pointer' : 'text-gray-400 cursor-default'
        )}
      >
        <span>{section.title}</span>
        {hasPages && (
          <svg
            className={clsx('w-4 h-4 transition-transform flex-shrink-0', isExpanded && 'rotate-90')}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        )}
      </button>
      {isExpanded && hasPages && (
        <div className="mt-0.5">
          {section.pages.map(page => (
            <NavLink
              key={page.slug}
              to={page.slug}
              onClick={onNavigate}
              className={({ isActive }) =>
                clsx(
                  'block py-2 px-3 pl-7 text-sm rounded-md transition-colors',
                  isActive
                    ? 'bg-ios-blue/10 text-ios-blue font-medium'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-navy'
                )
              }
            >
              {page.title}
            </NavLink>
          ))}
        </div>
      )}
    </div>
  )
}
