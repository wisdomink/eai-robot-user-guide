import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChatKit, useChatKit } from '@openai/chatkit-react'
import clsx from 'clsx'
import { useChatState } from '@/hooks/useChatState'

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

const BUILD_VERSION = (() => {
  const d = new Date(__BUILD_TIME__)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}.${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`
})()

const GREETING = 'Hi! I can help you with any of our robot products. Pick one to get started.'
const PROMPTS = [
  { label: 'FF Master Ultra', prompt: 'Tell me about FF Master Ultra. What are its key features, specs, and how do I get started?' },
  { label: 'FF Futurist Ultra', prompt: 'Tell me about FF Futurist Ultra. What are its key features, specs, and how do I get started?' },
  { label: 'FF Aegis Ultra', prompt: 'Tell me about FF Aegis Ultra. What are its key features, specs, and how do I get started?' },
  { label: 'FF Aegis EDU', prompt: 'Tell me about FF Aegis EDU. What are its key features, specs, and how do I get started?' },
]

type OverlayMode = 'buttons' | 'sending' | null

export default function ChatPanel() {
  const { isChatOpen } = useChatState()
  const [overlayMode, setOverlayMode] = useState<OverlayMode>('buttons')
  const [askingOwn, setAskingOwn] = useState(false)
  const navigate = useNavigate()
  const panelRef = useRef<HTMLDivElement>(null)

  const setThreadIdRef = useRef<((id: string | null) => Promise<void>) | null>(null)

  const handleNewChat = useCallback(() => {
    setThreadIdRef.current?.(null)
    setOverlayMode('buttons')
    setAskingOwn(false)
  }, [])

  const greetingText = askingOwn ? 'What can I help with today?' : '\u200B'

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
      greeting: greetingText,
    },
    composer: {
      placeholder: 'Ask a question…',
    },
    onResponseStart: () => {
      setOverlayMode(null)
    },
    onThreadChange: ({ threadId }: { threadId: string | null }) => {
      if (threadId === null) {
        setOverlayMode('buttons')
        setAskingOwn(false)
      }
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
    setOverlayMode('sending')
    sendUserMessage({ text: prompt })
  }, [sendUserMessage])

  const handleAskOwn = useCallback(() => {
    setAskingOwn(true)
    setOverlayMode(null)
    focusComposer()
  }, [focusComposer])

  return (
    <div ref={panelRef} className={clsx('chat-panel', isChatOpen && 'open')} id="chatPanel">
      <div className="chatkit-body">
        <ChatKit control={control} />
        {overlayMode && (
          <div className="ck-greeting-overlay">
            {overlayMode === 'buttons' && (
              <>
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
                <p className="ck-greeting-version">v{BUILD_VERSION}</p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
