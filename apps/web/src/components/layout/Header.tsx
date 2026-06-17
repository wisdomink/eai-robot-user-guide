import { useEffect, useRef, useState } from 'react'
import logoDark from '@/assets/icons/logo-dark.svg'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import {
  fetchManualDownloadConfig,
  getDefaultManualDownloadItems,
  type ManualDownloadItem,
} from '@/api/manualDownloadConfig'

interface HeaderProps {
  onMenuToggle: () => void
}

export default function Header({ onMenuToggle }: HeaderProps) {
  const isDesktop = useIsDesktop()
  const [isDownloadMenuOpen, setIsDownloadMenuOpen] = useState(false)
  const [manualDownloads, setManualDownloads] = useState<ManualDownloadItem[]>(() => getDefaultManualDownloadItems())
  const [downloadingProductId, setDownloadingProductId] = useState<string | null>(null)
  const downloadMenuRef = useRef<HTMLDivElement>(null)

  function getDownloadFilename(url: string, fallbackLabel: string) {
    try {
      const pathname = new URL(url).pathname
      const lastSegment = pathname.split('/').filter(Boolean).pop()
      if (!lastSegment) return `${fallbackLabel}.pdf`
      return decodeURIComponent(lastSegment).replace(/\+/g, ' ')
    } catch {
      return `${fallbackLabel}.pdf`
    }
  }

  async function handleDownload(product: ManualDownloadItem) {
    setDownloadingProductId(product.product_id)
    try {
      const response = await fetch(product.download_url)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const blob = await response.blob()
      const objectUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = objectUrl
      link.download = getDownloadFilename(product.download_url, product.label)
      link.rel = 'noopener'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 1000)
      setIsDownloadMenuOpen(false)
    } catch (error) {
      console.error('Manual download failed', error)
      window.alert('下载失败，请检查文件地址或服务器跨域配置。')
    } finally {
      setDownloadingProductId(null)
    }
  }

  useEffect(() => {
    if (!isDesktop) {
      setIsDownloadMenuOpen(false)
    }
  }, [isDesktop])

  useEffect(() => {
    let cancelled = false

    async function loadManualDownloads() {
      try {
        const config = await fetchManualDownloadConfig()
        if (!cancelled) {
          setManualDownloads(config.manual_downloads)
        }
      } catch {
        if (!cancelled) {
          setManualDownloads(getDefaultManualDownloadItems())
        }
      }
    }

    loadManualDownloads()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!isDownloadMenuOpen) {
      return
    }

    function handlePointerDown(event: MouseEvent) {
      if (downloadMenuRef.current && !downloadMenuRef.current.contains(event.target as Node)) {
        setIsDownloadMenuOpen(false)
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsDownloadMenuOpen(false)
      }
    }

    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isDownloadMenuOpen])

  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between h-[var(--header-height)] px-[clamp(12px,1.2vw,24px)] bg-white border-b border-gray-200">
      <div className="flex items-center">
        <button
          onClick={onMenuToggle}
          className="p-[clamp(4px,0.5vw,10px)] text-navy hover:bg-gray-100 rounded-md transition-colors"
          aria-label="Toggle sidebar"
        >
          <svg
            className="w-[var(--icon-sm)] h-[var(--icon-sm)]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
      </div>

      <div className="flex items-center gap-3">
        {isDesktop && (
          <div className="relative" ref={downloadMenuRef}>
            <button
              type="button"
              onClick={() => setIsDownloadMenuOpen(prev => !prev)}
              className="inline-flex items-center gap-2 rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-navy hover:bg-gray-50 transition-colors"
              aria-haspopup="menu"
              aria-expanded={isDownloadMenuOpen}
              aria-label="Download product PDF"
            >
              <span>Download</span>
              <svg
                className={`h-4 w-4 text-gray-500 transition-transform ${isDownloadMenuOpen ? 'rotate-180' : ''}`}
                viewBox="0 0 20 20"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M5 8l5 5 5-5" />
              </svg>
            </button>

            {isDownloadMenuOpen && (
              <div
                className="absolute right-0 top-[calc(100%+8px)] w-64 overflow-hidden rounded-xl border border-gray-200 bg-white shadow-lg"
                role="menu"
                aria-label="Product downloads"
              >
                {manualDownloads.map(product => (
                  <button
                    type="button"
                    key={product.product_id}
                    onClick={() => void handleDownload(product)}
                    disabled={downloadingProductId === product.product_id}
                    className="flex w-full items-center justify-between px-4 py-3 text-left text-sm text-navy hover:bg-purple/5 transition-colors border-b border-gray-100 last:border-b-0 disabled:cursor-wait disabled:opacity-70"
                    role="menuitem"
                  >
                    <span>
                      {downloadingProductId === product.product_id ? `Downloading ${product.label}...` : product.label}
                    </span>
                    <svg
                      className="h-4 w-4 text-purple"
                      viewBox="0 0 20 20"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.8"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M10 3v9" />
                      <path d="M6.5 9.5L10 13l3.5-3.5" />
                      <path d="M4 16h12" />
                    </svg>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <a href="https://www.ff.com/" className="p-[clamp(2px,0.3vw,6px)]">
          <img
            src={logoDark}
            alt="EAI Robot"
            className="h-[var(--icon-md)] w-[var(--icon-md)]"
          />
        </a>
      </div>
    </header>
  )
}
