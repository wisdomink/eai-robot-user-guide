import clsx from 'clsx'
import iconClose from '@/assets/icons/icon-close.svg'
import Sidebar from './Sidebar'

interface MobileMenuDrawerProps {
  isOpen: boolean
  onClose: () => void
}

export default function MobileMenuDrawer({ isOpen, onClose }: MobileMenuDrawerProps) {
  return (
    <>
      {/* Backdrop */}
      <div
        className={clsx(
          'fixed inset-0 bg-black/40 z-50 transition-opacity lg:hidden',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        className={clsx(
          'fixed top-0 left-0 bottom-0 w-72 bg-white z-50 transform transition-transform lg:hidden overflow-y-auto',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <span className="font-rubik font-semibold text-navy">Navigation</span>
          <button onClick={onClose} className="p-1" aria-label="Close menu">
            <img src={iconClose} alt="" className="w-5 h-5" />
          </button>
        </div>
        <Sidebar onNavigate={onClose} />
      </div>
    </>
  )
}
