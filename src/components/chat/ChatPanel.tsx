import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChatKit, useChatKit } from '@openai/chatkit-react'

const CHATKIT_API_URL = import.meta.env.VITE_CHATKIT_API_URL || 'http://localhost:8000/chatkit'
const CHATKIT_DOMAIN_KEY = import.meta.env.VITE_CHATKIT_DOMAIN_KEY || 'local-dev'

export default function ChatPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const navigate = useNavigate()
  const panelRef = useRef<HTMLDivElement>(null)

  const handleClose = useCallback(() => setIsOpen(false), [])

  const { control } = useChatKit({
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

  // Style internal links as buttons and intercept clicks for SPA navigation.
  // ChatKit renders [title](url) as <a> tags; we apply inline button styles
  // via MutationObserver (survives ChatKit re-renders because we only add
  // attributes to existing elements, never replace DOM nodes).
  useEffect(() => {
    const panel = panelRef.current
    if (!panel) return

    const BUTTON_STYLE = [
      'display:inline-block',
      'padding:5px 16px',
      'margin:3px 4px',
      'border-radius:6px',
      'font-size:13px',
      'font-weight:500',
      'line-height:1.5',
      'color:#6965E0',
      'background:rgba(105,101,224,0.08)',
      'border:1px solid rgba(105,101,224,0.25)',
      'text-decoration:none',
      'cursor:pointer',
      'transition:all .15s ease',
    ].join(';')

    const styleLinks = () => {
      panel.querySelectorAll<HTMLAnchorElement>('a[href^="/"]').forEach(link => {
        if (link.hasAttribute('data-ref-btn')) return
        link.setAttribute('data-ref-btn', '')
        link.style.cssText = BUTTON_STYLE
        link.onmouseenter = () => {
          link.style.background = 'rgba(105,101,224,0.18)'
          link.style.borderColor = '#6965E0'
        }
        link.onmouseleave = () => {
          link.style.background = 'rgba(105,101,224,0.08)'
          link.style.borderColor = 'rgba(105,101,224,0.25)'
        }
      })
    }

    let timer: ReturnType<typeof setTimeout> | null = null
    const schedule = () => {
      if (timer) clearTimeout(timer)
      timer = setTimeout(styleLinks, 120)
    }

    const observer = new MutationObserver(schedule)
    observer.observe(panel, { childList: true, subtree: true })
    styleLinks()

    const handleClick = (e: Event) => {
      const anchor = (e.target as HTMLElement).closest('a')
      if (!anchor) return
      const href = anchor.getAttribute('href')
      if (!href || !href.startsWith('/')) return

      e.preventDefault()
      e.stopPropagation()

      const url = new URL(href, window.location.origin)
      navigate(url.pathname)
      if (url.hash) {
        setTimeout(() => {
          document.getElementById(url.hash.slice(1))
            ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }, 300)
      }
    }

    panel.addEventListener('click', handleClick, true)

    return () => {
      observer.disconnect()
      if (timer) clearTimeout(timer)
      panel.removeEventListener('click', handleClick, true)
    }
  }, [navigate])

  return (
    <div ref={panelRef} className={`chat-panel${isOpen ? ' open' : ''}`} id="chatPanel">
      <div className="chatkit-body">
        <ChatKit control={control} />
      </div>
    </div>
  )
}
