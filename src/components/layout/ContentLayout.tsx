import { useSidebarState } from '@/hooks/useSidebarState'
import Header from './Header'
import Sidebar from './Sidebar'
import MobileMenuDrawer from './MobileMenuDrawer'
import SearchInfoBar from '@/components/search/SearchInfoBar'

interface ContentLayoutProps {
  children: React.ReactNode
}

export default function ContentLayout({ children }: ContentLayoutProps) {
  const { isOpen, toggle, close } = useSidebarState()

  return (
    <div className="min-h-screen bg-white">
      <Header onMenuToggle={toggle} />

      {/* Desktop sidebar */}
      <aside className="hidden lg:block fixed left-0 top-16 bottom-0 w-64 border-r border-gray-200 overflow-y-auto bg-white">
        <Sidebar />
      </aside>

      {/* Mobile drawer */}
      <MobileMenuDrawer isOpen={isOpen} onClose={close} />

      {/* Main content */}
      <main className="lg:ml-64 min-h-[calc(100vh-4rem)]">
        <SearchInfoBar />
        <div className="max-w-4xl mx-auto px-4 md:px-8 lg:px-12 py-6 md:py-10">
          {children}
        </div>
      </main>
    </div>
  )
}
