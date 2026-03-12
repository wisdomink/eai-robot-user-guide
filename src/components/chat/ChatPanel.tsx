import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChatKit, useChatKit } from '@openai/chatkit-react'

const CHAT_MODE = import.meta.env.VITE_CHAT_MODE || 'backend'
const CHATKIT_API_URL = import.meta.env.VITE_CHATKIT_API_URL || '/chatkit'
const CHATKIT_DOMAIN_KEY = import.meta.env.VITE_CHATKIT_DOMAIN_KEY || 'local-dev'
const SESSION_ENDPOINT = import.meta.env.VITE_CHATKIT_SESSION_URL || '/api/chatkit/session'

function buildApiConfig() {
  if (CHAT_MODE === 'agent-builder') {
    return {
      async getClientSecret(_existing: string | null) {
        const res = await fetch(SESSION_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user: `web-${crypto.randomUUID?.() ?? Date.now()}`,
          }),
        })
        const { client_secret } = await res.json()
        return client_secret as string
      },
    }
  }
  return {
    url: CHATKIT_API_URL,
    domainKey: CHATKIT_DOMAIN_KEY,
  }
}

const GREETING = 'Hi! I can help you with any of our robot products. Pick one to get started.'
const PROMPTS = [
  { label: 'FF Master Ultra', prompt: 'Tell me about FF Master Ultra. What are its key features, specs, and how do I get started?' },
  { label: 'FF Futurist Ultra', prompt: 'Tell me about FF Futurist Ultra. What are its key features, specs, and how do I get started?' },
  { label: 'FF Aegis Ultra', prompt: 'Tell me about FF Aegis Ultra. What are its key features, specs, and how do I get started?' },
  { label: 'FF Aegis EDU', prompt: 'Tell me about FF Aegis EDU. What are its key features, specs, and how do I get started?' },
]

const isDesktop = () => window.innerWidth >= 1024

export default function ChatPanel() {
  const [isOpen, setIsOpen] = useState(isDesktop)
  const [showGreeting, setShowGreeting] = useState(true)
  const navigate = useNavigate()
  const panelRef = useRef<HTMLDivElement>(null)

  const setThreadIdRef = useRef<((id: string | null) => Promise<void>) | null>(null)

  const handleNewChat = useCallback(() => {
    setThreadIdRef.current?.(null)
    setShowGreeting(true)
  }, [])

  const { sendUserMessage, focusComposer, setThreadId, control } = useChatKit({
    locale: 'en',
    api: buildApiConfig(),
    header: {
      title: { text: 'Ask AI' },
      rightAction: {
        icon: 'close',
        onClick: handleNewChat,
      },
    },
    history: {
      enabled: false,
    },
    startScreen: {
      greeting: ' ',
    },
    composer: {
      placeholder: 'Ask a question…',
    },
    disclaimer: {
      text: 'Answers are based solely on the manual content.',
    },
    onResponseStart: () => {
      setShowGreeting(false)
    },
    onThreadChange: ({ threadId }: { threadId: string | null }) => {
      if (threadId === null) setShowGreeting(true)
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

  setThreadIdRef.current = setThreadId

  const handlePromptClick = useCallback((prompt: string) => {
    setShowGreeting(false)
    sendUserMessage({ text: prompt })
  }, [sendUserMessage])

  const handleAskOwn = useCallback(() => {
    setShowGreeting(false)
    focusComposer()
  }, [focusComposer])

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
        {showGreeting && (
          <div className="ck-greeting-overlay">
            <p className="ck-greeting-text">{GREETING}</p>
            <div className="ck-greeting-prompts">
              {PROMPTS.map((p) => (
                <button
                  key={p.label}
                  className="ck-greeting-prompt-btn"
                  onClick={() => handlePromptClick(p.prompt)}
                >
                  {p.label}
                </button>
              ))}
              <button
                className="ck-greeting-prompt-btn ck-greeting-prompt-ask"
                onClick={handleAskOwn}
              >
                Ask your own question →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
