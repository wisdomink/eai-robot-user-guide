import { useState } from 'react'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import Header from './Header'
import Sidebar from './Sidebar'
import MobileMenuDrawer from './MobileMenuDrawer'
import SearchInfoBar from '@/components/search/SearchInfoBar'
import clsx from 'clsx'

interface ContentLayoutProps {
  children: React.ReactNode
  fullWidth?: boolean
}

export default function ContentLayout({ children, fullWidth }: ContentLayoutProps) {
  const isDesktop = useIsDesktop()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const toggle = () => setSidebarOpen(prev => !prev)
  const close = () => setSidebarOpen(false)

  return (
    <div className="min-h-screen bg-white">
      <Header onMenuToggle={toggle} />

      {/* Desktop sidebar */}
      {isDesktop && (
        <aside
          className={clsx(
            'fixed left-0 top-[var(--header-height)] bottom-0 w-[var(--sidebar-width)] border-r border-gray-200 overflow-y-auto bg-white transition-transform duration-200 z-40',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <Sidebar />
        </aside>
      )}

      {/* Mobile drawer */}
      {!isDesktop && (
        <MobileMenuDrawer isOpen={sidebarOpen} onClose={close} />
      )}

      {/* Main content */}
      <main
        className={clsx(
          'min-h-[calc(100vh-var(--header-height))] transition-[margin] duration-200',
          isDesktop && sidebarOpen ? 'ml-[var(--sidebar-width)]' : 'ml-0'
        )}
      >
        <SearchInfoBar />
        <div
          className={clsx(
            fullWidth
              ? 'px-4 md:px-8 lg:px-10 py-4 md:py-6'
              : 'max-w-4xl mx-auto px-4 md:px-8 lg:px-12 py-6 md:py-10'
          )}
        >
          {children}
        </div>
      </main>
    </div>
  )
}
