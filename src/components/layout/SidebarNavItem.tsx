import { useState } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import clsx from 'clsx'
import type { SectionConfig } from '@/content'

interface SidebarNavItemProps {
  section: SectionConfig
  onNavigate?: () => void
}

export default function SidebarNavItem({ section, onNavigate }: SidebarNavItemProps) {
  const location = useLocation()
  const navigate = useNavigate()

  const isChildActive = section.pages.some(page => page.slug === location.pathname)
  const [isExpanded, setIsExpanded] = useState(isChildActive)

  const hasPages = section.pages.length > 0
  const isSinglePage = section.pages.length === 1

  const handleSectionClick = () => {
    if (!hasPages) return
    if (isSinglePage) {
      // Single-page sections: navigate directly to the only page
      navigate(section.pages[0].slug)
      onNavigate?.()
    } else {
      setIsExpanded(!isExpanded)
    }
  }

  return (
    <div>
      <button
        onClick={handleSectionClick}
        className={clsx(
          'w-full flex items-center gap-1.5 py-2 px-3 text-left text-[var(--fs-sidebar)] font-roboto rounded-md transition-colors',
          'font-normal text-navy',
          hasPages ? 'hover:bg-gray-100 cursor-pointer' : 'text-gray-400 cursor-default',
          isSinglePage && isChildActive && 'bg-purple/10 text-purple'
        )}
      >
        {/* Chevron on the LEFT of text — hidden for single-page sections */}
        {hasPages && !isSinglePage && (
          <svg
            className={clsx(
              'w-[clamp(14px,1vw,18px)] h-[clamp(14px,1vw,18px)] transition-transform flex-shrink-0',
              isExpanded ? 'rotate-90' : 'rotate-0'
            )}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        )}
        {/* Spacer for items without chevron to keep text aligned */}
        {(!hasPages || isSinglePage) && <span className="w-[clamp(14px,1vw,18px)] flex-shrink-0" />}
        <span>{section.title}</span>
      </button>
      {/* Don't show sub-pages for single-page sections — title IS the link */}
      {isExpanded && hasPages && !isSinglePage && (
        <div className="mt-0.5">
          {section.pages.map(page => (
            <NavLink
              key={page.slug}
              to={page.slug}
              onClick={onNavigate}
              className={({ isActive }) =>
                clsx(
                  'block py-2 px-3 pl-10 text-[var(--fs-sidebar)] transition-colors',
                  isActive
                    ? 'bg-purple/10 text-purple font-medium'
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
