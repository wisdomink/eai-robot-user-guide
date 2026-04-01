import { useState, useCallback, useMemo, type FormEvent } from 'react'
import { ChatKit, useChatKit } from '@openai/chatkit-react'
import clsx from 'clsx'
import './chat-panel.css'

const CHATKIT_DOMAIN_KEY = import.meta.env.VITE_CHATKIT_DOMAIN_KEY || 'local-dev'
const CHATKIT_THREAD_STORAGE_KEY = 'ffrobot:chatkit:thread-id'

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

function readStoredThreadId() {
  if (typeof window === 'undefined') return null
  return window.sessionStorage.getItem(CHATKIT_THREAD_STORAGE_KEY)
}

function persistThreadId(threadId: string | null) {
  if (typeof window === 'undefined') return
  if (threadId) {
    window.sessionStorage.setItem(CHATKIT_THREAD_STORAGE_KEY, threadId)
    return
  }
  window.sessionStorage.removeItem(CHATKIT_THREAD_STORAGE_KEY)
}

const BUILD_VERSION = (() => {
  const d = new Date(__BUILD_TIME__)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}.${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`
})()

const GREETING = 'Hi! I can help you with any of our products. Pick one to get started.'
const PROMPTS = [
  { label: 'FF Master', prompt: 'Tell me about FF Master. What are its key features, specs, and how do I get started?' },
  { label: 'FF Futurist', prompt: 'Tell me about FF Futurist. What are its key features, specs, and how do I get started?' },
  { label: 'FF Futurist Ultra', prompt: 'Tell me about FF Futurist Ultra. What are its key features, specs, and how do I get started?' },
  { label: 'FF Aegis', prompt: 'Tell me about FF Aegis. What are its key features, specs, and how do I get started?' },
  { label: 'FF Aegis Ultra', prompt: 'Tell me about FF Aegis Ultra. What are its key features, specs, and how do I get started?' },
  { label: 'FF 91 2.0', prompt: 'Tell me about the FF 91 2.0. What are its key features, specs, and how do I get started?' },
]

type OverlayMode = 'buttons' | null

export interface ChatPromptOption {
  label: string
  prompt: string
}

export interface ChatPanelApiConfig {
  url: string
  domainKey: string
}

export interface ChatEntityNavigatePayload {
  url: URL
  slug: string
  entity: {
    data?: {
      slug?: string
      [key: string]: unknown
    }
    [key: string]: unknown
  }
}

export interface ChatPanelProps {
  open?: boolean
  defaultOpen?: boolean
  onOpenChange?: (open: boolean) => void
  onEntityNavigate?: (payload: ChatEntityNavigatePayload) => void
  apiConfig?: ChatPanelApiConfig
  panelId?: string
  className?: string
  title?: string
  placeholder?: string
  greeting?: string
  prompts?: ChatPromptOption[]
  fabLabel?: string
  fabAriaLabel?: string
  showFab?: boolean
  buildVersion?: string
}

function useControllableOpen(
  open: boolean | undefined,
  defaultOpen: boolean,
  onOpenChange?: (open: boolean) => void,
) {
  const [internalOpen, setInternalOpen] = useState(defaultOpen)
  const isControlled = open !== undefined
  const isOpen = isControlled ? open : internalOpen

  const setOpen = useCallback((nextOpen: boolean) => {
    if (!isControlled) {
      setInternalOpen(nextOpen)
    }
    onOpenChange?.(nextOpen)
  }, [isControlled, onOpenChange])

  return [isOpen, setOpen] as const
}

export default function ChatPanel({
  open,
  defaultOpen = false,
  onOpenChange,
  onEntityNavigate,
  apiConfig,
  panelId = 'chatPanel',
  className,
  title = 'FF AI',
  placeholder = 'Ask a question…',
  greeting = GREETING,
  prompts = PROMPTS,
  fabLabel = 'ChatAI',
  fabAriaLabel = 'Open Chat AI',
  showFab = true,
  buildVersion = BUILD_VERSION,
}: ChatPanelProps) {
  const resolvedApiConfig = useMemo(() => apiConfig ?? buildApiConfig(), [apiConfig])
  const [activeThreadId, setActiveThreadId] = useState<string | null>(() => readStoredThreadId())
  const [isChatOpen, setIsChatOpen] = useControllableOpen(open, defaultOpen, onOpenChange)
  const [overlayMode, setOverlayMode] = useState<OverlayMode>(() => (
    readStoredThreadId() ? null : 'buttons'
  ))
  const [inputValue, setInputValue] = useState('')

  const openChat = useCallback(() => {
    setIsChatOpen(true)
  }, [setIsChatOpen])

  const closeChat = useCallback(() => {
    setIsChatOpen(false)
  }, [setIsChatOpen])

  const { sendUserMessage, control } = useChatKit({
    locale: 'en',
    api: resolvedApiConfig,
    initialThread: activeThreadId,
    header: {
      title: { text: title },
      rightAction: {
        icon: 'collapse-small',
        onClick: closeChat,
      },
    },
    history: {
      enabled: false,
    },
    startScreen: {
      greeting: '\u200B',
    },
    composer: {
      placeholder,
    },
    onResponseStart: () => {
      setOverlayMode(null)
    },
    onThreadChange: ({ threadId }: { threadId: string | null }) => {
      setActiveThreadId(threadId)
      persistThreadId(threadId)
      if (threadId === null) {
        setOverlayMode('buttons')
        setInputValue('')
        return
      }
      setOverlayMode(null)
    },
    entities: {
      onClick: (entity) => {
        const slug = entity.data?.slug
        if (!slug) return
        try {
          const url = new URL(slug, window.location.origin)
          onEntityNavigate?.({ url, slug, entity })
        } catch {
          if (import.meta.env.DEV) {
            console.warn('[ChatPanel] Invalid entity slug:', slug)
          }
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
    <>
      {showFab && (
        <button
          type="button"
          className={clsx('chat-fab', isChatOpen && 'hidden')}
          onClick={openChat}
          aria-label={fabAriaLabel}
          aria-controls={panelId}
          aria-expanded={isChatOpen}
        >
          <span className="chat-fab-icon" aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M20 4H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h3v4l4-4h9a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
              <circle cx="8" cy="11" r="1.1" fill="currentColor" />
              <circle cx="12" cy="11" r="1.1" fill="currentColor" />
              <circle cx="16" cy="11" r="1.1" fill="currentColor" />
            </svg>
          </span>
          <span className="chat-fab-label">{fabLabel}</span>
        </button>
      )}

      <div
        className={clsx('chat-panel', isChatOpen && 'open', className)}
        id={panelId}
        aria-hidden={!isChatOpen}
      >
        <div className="chatkit-body">
          <ChatKit control={control} />
          {overlayMode && (
            <div className="ck-greeting-overlay">
              {overlayMode === 'buttons' && (
                <>
                  <div className="ck-greeting-center">
                    <p className="ck-greeting-text">{greeting}</p>
                    <div className="ck-greeting-prompts">
                      {prompts.map((p) => (
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
                        placeholder={placeholder}
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
                    <p className="ck-greeting-version">v{buildVersion}</p>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
