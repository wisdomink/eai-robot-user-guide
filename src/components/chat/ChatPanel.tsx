import { useState, useCallback, useRef, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChatKit, useChatKit } from '@openai/chatkit-react'
import clsx from 'clsx'
import { useChatState } from '@/hooks/useChatState'

const CHATKIT_DOMAIN_KEY = import.meta.env.VITE_CHATKIT_DOMAIN_KEY || 'local-dev'

function resolveChatKitApiUrl() {
  const raw = import.meta.env.VITE_CHATKIT_API_URL
  if (!raw) return '/api/chatkit'
  if (/^https?:\/\//.test(raw)) {
    const parsed = new URL(raw)
    parsed.pathname = '/api/chatkit'
    return parsed.toString()
  }
  return '/api/chatkit'
}

function buildApiConfig() {
  return {
    url: resolveChatKitApiUrl(),
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
  { label: 'FF 91 2.0', prompt: 'Tell me about the FF 91 2.0. What are its key features, specs, and how do I get started?' },
]

type OverlayMode = 'buttons' | null

export default function ChatPanel() {
  const { isChatOpen } = useChatState()
  const [overlayMode, setOverlayMode] = useState<OverlayMode>('buttons')
  const [inputValue, setInputValue] = useState('')
  const navigate = useNavigate()
  const panelRef = useRef<HTMLDivElement>(null)

  const setThreadIdRef = useRef<((id: string | null) => Promise<void>) | null>(null)

  const overlayModeRef = useRef<OverlayMode>(overlayMode)
  overlayModeRef.current = overlayMode

  const handleNewChat = useCallback(() => {
    if (overlayModeRef.current === 'buttons') return
    setThreadIdRef.current?.(null)
    setOverlayMode('buttons')
    setInputValue('')
  }, [])

  const { sendUserMessage, setThreadId, control } = useChatKit({
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
      greeting: '\u200B',
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
        setInputValue('')
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
    setOverlayMode(null)
    sendUserMessage({ text: prompt })
  }, [sendUserMessage])

  const handleInputSend = useCallback((e?: FormEvent) => {
    e?.preventDefault()
    const text = inputValue.trim()
    if (!text) return
    setInputValue('')
    setOverlayMode(null)
    sendUserMessage({ text })
  }, [inputValue, sendUserMessage])

  return (
    <div ref={panelRef} className={clsx('chat-panel', isChatOpen && 'open')} id="chatPanel">
      <div className="chatkit-body">
        <ChatKit control={control} />
        {overlayMode && (
          <div className="ck-greeting-overlay">
            {overlayMode === 'buttons' && (
              <>
                <div className="ck-greeting-center">
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
                  </div>
                </div>
                <div className="ck-greeting-bottom">
                  <form className="ck-greeting-input-bar" onSubmit={handleInputSend}>
                    <input
                      type="text"
                      className="ck-greeting-input"
                      placeholder="Ask a question…"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                    />
                    <button
                      type="submit"
                      className="ck-greeting-send-btn"
                      disabled={!inputValue.trim()}
                      aria-label="Send"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 3a1 1 0 0 1 .707.293l6 6a1 1 0 0 1-1.414 1.414L13 6.414V20a1 1 0 1 1-2 0V6.414l-4.293 4.293a1 1 0 0 1-1.414-1.414l6-6A1 1 0 0 1 12 3z" />
                      </svg>
                    </button>
                  </form>
                  <p className="ck-greeting-version">v{BUILD_VERSION}</p>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
