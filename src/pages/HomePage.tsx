import { useEffect, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import logoDark from '@/assets/icons/logo-dark.svg'
import iconMenu from '@/assets/icons/icon-menu.svg'
import { sidebarConfig } from '@/content'
import MarkdownRenderer from '@/components/markdown/MarkdownRenderer'
import { getPageContent } from '@/content'
import { useState } from 'react'
import clsx from 'clsx'

export default function HomePage() {
  const navigate = useNavigate()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    document.title = 'FF Master Ultra Edition - User Manual'
  }, [])

  // Handle SPA link clicks in markdown content
  const handleContentClick = useCallback(
    (e: React.MouseEvent) => {
      const target = (e.target as HTMLElement).closest('a[data-spa-link]') as HTMLAnchorElement | null
      if (target) {
        e.preventDefault()
        const href = target.getAttribute('href')
        if (href) navigate(href)
      }
    },
    [navigate]
  )

  const homeContent = getPageContent('home.md')

  // Build sidebar items from config
  const sidebarItems = [
    { label: sidebarConfig.title, path: '/product-overview', active: true },
    ...sidebarConfig.sections.map(section => ({
      label: section.title,
      path: section.pages[0]?.slug,
      active: false,
    })),
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Bar */}
      <header className="sticky top-0 z-50 flex items-center justify-between h-16 px-4 lg:px-10 bg-white border-b border-gray-100">
        <div className="flex items-center gap-3">
          <button
            className="lg:hidden p-2 -ml-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <img src={iconMenu} alt="" className="w-6 h-6" />
          </button>
          <Link to="/" className="flex items-center">
            <img src={logoDark} alt="EAI Robot" className="h-10 w-10" />
          </Link>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar - Desktop */}
        <aside className="hidden lg:block w-[363px] flex-shrink-0 bg-white border-r border-gray-100">
          <div className="p-8 pb-4">
            <nav className="space-y-1">
              {sidebarItems.map((item, i) => (
                <button
                  key={i}
                  onClick={() => item.path && navigate(item.path)}
                  className={clsx(
                    'w-full text-left px-3 py-2 rounded-md text-body font-roboto transition-colors',
                    item.active
                      ? 'bg-gray-500/8 font-medium text-navy'
                      : item.path
                        ? 'text-gray-600 hover:bg-gray-100'
                        : 'text-gray-400 cursor-default'
                  )}
                >
                  {item.label}
                </button>
              ))}
            </nav>
          </div>
        </aside>

        {/* Mobile sidebar overlay */}
        {mobileMenuOpen && (
          <>
            <div className="fixed inset-0 bg-black/40 z-40 lg:hidden" onClick={() => setMobileMenuOpen(false)} />
            <aside className="fixed top-0 left-0 bottom-0 w-72 bg-white z-50 lg:hidden overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <span className="font-rubik font-semibold text-navy">Navigation</span>
                  <button onClick={() => setMobileMenuOpen(false)} className="text-gray-500 text-xl">&times;</button>
                </div>
                <nav className="space-y-1">
                  {sidebarItems.map((item, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        if (item.path) {
                          navigate(item.path)
                          setMobileMenuOpen(false)
                        }
                      }}
                      className={clsx(
                        'w-full text-left px-3 py-2 rounded-md text-sm transition-colors',
                        item.active ? 'bg-gray-100 font-medium text-navy' : item.path ? 'text-gray-600 hover:bg-gray-100' : 'text-gray-400 cursor-default'
                      )}
                    >
                      {item.label}
                    </button>
                  ))}
                </nav>
              </div>
            </aside>
          </>
        )}

        {/* Main content - Home page with cover */}
        <main className="flex-1 min-h-[calc(100vh-4rem)]">
          {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions */}
          <div onClick={handleContentClick} className="h-full">
            <MarkdownRenderer content={homeContent} className="home-content" />
          </div>
        </main>
      </div>
    </div>
  )
}
