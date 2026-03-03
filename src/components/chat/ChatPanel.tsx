import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChatKit, useChatKit } from '@openai/chatkit-react'

const SESSION_API_URL = import.meta.env.VITE_SESSION_API_URL || 'http://localhost:8000/api/chatkit/session'

export default function ChatPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const navigate = useNavigate()
  const panelRef = useRef<HTMLDivElement>(null)

  const handleClose = useCallback(() => setIsOpen(false), [])

  // Intercept internal link clicks for SPA navigation
  useEffect(() => {
    const panel = panelRef.current
    if (!panel) return

    const handleLinkClick = (e: MouseEvent) => {
      const anchor = (e.target as HTMLElement).closest('a')
      if (!anchor) return

      const href = anchor.getAttribute('href')
      if (!href || !href.startsWith('/')) return
      if (e.metaKey || e.ctrlKey || e.shiftKey) return

      e.preventDefault()
      navigate(href)
    }

    panel.addEventListener('click', handleLinkClick)
    return () => panel.removeEventListener('click', handleLinkClick)
  }, [navigate])

  const { control } = useChatKit({
    api: {
      async getClientSecret() {
        const res = await fetch(SESSION_API_URL, { method: 'POST' })
        if (!res.ok) throw new Error(`Session creation failed: ${res.status}`)
        const { client_secret } = await res.json()
        return client_secret
      },
    },
    header: {
      title: { text: 'Ask AI' },
      rightAction: {
        icon: 'close',
        onClick: handleClose,
      },
    },
    startScreen: {
      greeting: 'Ask anything about FF Master — I\'ll answer based on the documentation.',
      prompts: [
        { label: "What's in the package?", prompt: "What's in the package?" },
        { label: 'How do I charge?', prompt: 'How do I charge the robot?' },
        { label: 'Joint limits', prompt: 'What are the joint limits?' },
        { label: 'Emergency stop', prompt: 'How do I perform an emergency stop?' },
      ],
    },
    composer: {
      placeholder: 'Ask a question…',
    },
    disclaimer: {
      text: 'Answers are based solely on the manual content.',
    },
    entities: {
      onClick: (entity) => {
        const slug = entity.data?.slug
        if (!slug) return
        const url = new URL(slug, window.location.origin)
        navigate(url.pathname)
        if (url.hash) {
          setTimeout(() => {
            document.getElementById(url.hash.slice(1))
              ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }, 300)
        }
      },
    },
    theme: {
      colorScheme: 'light',
      color: {
        accent: { primary: '#6965E0', level: 2 },
      },
      density: 'compact',
      radius: 'round',
    },
  })

  useEffect(() => {
    const toggleBtn = document.getElementById('chatToggleBtn')
    const dot = document.getElementById('chatBtnDot')
    if (dot) dot.classList.add('show')
    const handleToggle = () => setIsOpen((prev) => !prev)
    toggleBtn?.addEventListener('click', handleToggle)
    return () => toggleBtn?.removeEventListener('click', handleToggle)
  }, [])

  useEffect(() => {
    const main = document.querySelector('main.main')
    const toggleBtn = document.getElementById('chatToggleBtn')
    main?.classList.toggle('chat-open', isOpen)
    toggleBtn?.classList.toggle('active', isOpen)
  }, [isOpen])

  return (
    <div ref={panelRef} className={`chat-panel${isOpen ? ' open' : ''}`} id="chatPanel">
      <div className="chatkit-body">
        <ChatKit control={control} />
      </div>
    </div>
  )
}
