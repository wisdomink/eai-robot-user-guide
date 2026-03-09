import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChatKit, useChatKit } from '@openai/chatkit-react'

const CHATKIT_API_URL = import.meta.env.VITE_CHATKIT_API_URL || '/chatkit'
const CHATKIT_DOMAIN_KEY = import.meta.env.VITE_CHATKIT_DOMAIN_KEY || 'local-dev'

const isDesktop = () => window.innerWidth >= 1024

export default function ChatPanel() {
  const [isOpen, setIsOpen] = useState(isDesktop)
  const navigate = useNavigate()
  const panelRef = useRef<HTMLDivElement>(null)

  const handleClose = useCallback(() => setIsOpen(false), [])

  const { control } = useChatKit({
    locale: 'en',
    api: {
      url: CHATKIT_API_URL,
      domainKey: CHATKIT_DOMAIN_KEY,
    },
    header: {
      title: { text: 'Ask AI' },
      rightAction: {
        icon: 'close',
        onClick: handleClose,
      },
    },
    history: {
      enabled: false,
    },
    startScreen: {
      greeting: 'Hi! I can help you with any of our robot products. Pick one to get started.',
      prompts: [
        { label: 'FF Master Ultra', prompt: 'Tell me about FF Master Ultra. What are its key features, specs, and how do I get started?' },
        { label: 'FF Futurist Ultra', prompt: 'Tell me about FF Futurist Ultra. What are its key features, specs, and how do I get started?' },
        { label: 'FF Aegis Ultra', prompt: 'Tell me about FF Aegis Ultra. What are its key features, specs, and how do I get started?' },
        { label: 'FF Aegis EDU', prompt: 'Tell me about FF Aegis EDU. What are its key features, specs, and how do I get started?' },
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
