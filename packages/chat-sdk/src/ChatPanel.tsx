import { useState, useCallback, useEffect, useRef, useMemo, type CSSProperties, type FormEvent } from 'react'
import { ChatKit, useChatKit } from '@openai/chatkit-react'
import clsx from 'clsx'
import { fetchHomepagePrompts, type HomepagePromptsConfig } from './homepagePromptsClient'
import { getDefaultChatkitApiUrl } from './chatEndpoints'

const isDev = Boolean(typeof import.meta !== 'undefined' && import.meta.env?.DEV)

const CHATKIT_THREAD_STORAGE_KEY = 'ffrobot:chatkit:thread-id'
const CHATKIT_DOMAIN_KEY = import.meta.env.VITE_CHATKIT_DOMAIN_KEY || 'local-dev'

function resolveChatKitApiUrl() {
  const raw = import.meta.env.VITE_CHATKIT_API_URL
  if (!raw) return getDefaultChatkitApiUrl()
  if (/^https?:\/\//.test(raw)) {
    return raw
  }
  return new URL(raw, window.location.origin).toString()
}

function buildApiConfig() {
  return {
    url: resolveChatKitApiUrl(),
    domainKey: CHATKIT_DOMAIN_KEY,
  }
}

function resolveBuildVersion() {
  if (typeof __BUILD_TIME__ !== 'string' || !__BUILD_TIME__) {
    return 'dev'
  }
  const d = new Date(__BUILD_TIME__)
  if (Number.isNaN(d.getTime())) {
    return 'dev'
  }
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}.${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`
}

function readStoredThreadId(storageKey: string) {
  if (typeof window === 'undefined') return null
  return window.sessionStorage.getItem(storageKey)
}

function persistThreadId(threadId: string | null, storageKey: string) {
  if (typeof window === 'undefined') return
  if (threadId) {
    window.sessionStorage.setItem(storageKey, threadId)
    return
  }
  window.sessionStorage.removeItem(storageKey)
}

const FALLBACK_GREETING = 'Hi! I can help you with any of our products. Pick one to get started.'
const FALLBACK_PLACEHOLDER = 'Ask a question…'
const FALLBACK_PROMPTS = [
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
      pageUrl?: string
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
  promptsApiUrl?: string | null
  fabLabel?: string
  fabAriaLabel?: string
  showFab?: boolean
  buildVersion?: string
  storageKey?: string
  zIndex?: number
  rootClassName?: string
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

const SOURCE_HEADING_RE = /^(参考来源|Sources)$/i

function hideSourceSections(root: HTMLElement) {
  const headings = root.querySelectorAll('h2')
  for (const h2 of headings) {
    if (h2.dataset.srcHidden) continue
    const text = (h2.textContent || '').trim()
    if (!SOURCE_HEADING_RE.test(text)) continue
    h2.dataset.srcHidden = '1'
    h2.style.display = 'none'
    let sibling = h2.nextElementSibling
    while (sibling) {
      ;(sibling as HTMLElement).style.display = 'none'
      sibling = sibling.nextElementSibling
    }
  }
}

function useSourceSectionHider(containerRef: React.RefObject<HTMLDivElement | null>) {
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    let pending = 0
    function scan() {
      pending = 0
      hideSourceSections(container!)
    }
    function scheduleScan() {
      if (!pending) pending = requestAnimationFrame(scan)
    }

    scan()

    const observer = new MutationObserver(scheduleScan)
    observer.observe(container, { childList: true, subtree: true, characterData: true })
    return () => {
      observer.disconnect()
      if (pending) cancelAnimationFrame(pending)
    }
  }, [containerRef])
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
  placeholder: placeholderProp = FALLBACK_PLACEHOLDER,
  greeting: greetingProp = FALLBACK_GREETING,
  prompts: promptsProp = FALLBACK_PROMPTS,
  promptsApiUrl,
  fabLabel = 'ChatAI',
  fabAriaLabel = 'Open Chat AI',
  showFab = true,
  buildVersion = resolveBuildVersion(),
  storageKey = CHATKIT_THREAD_STORAGE_KEY,
  zIndex,
  rootClassName,
}: ChatPanelProps) {
  const chatkitBodyRef = useRef<HTMLDivElement>(null)
  useSourceSectionHider(chatkitBodyRef)

  const resolvedApiConfig = useMemo(() => apiConfig ?? buildApiConfig(), [apiConfig])
  const rootStyle = useMemo(() => {
    if (zIndex === undefined) return undefined
    return {
      '--ffrobot-chat-panel-z-index': String(zIndex),
      '--ffrobot-chat-fab-z-index': String(zIndex + 10),
    } as CSSProperties
  }, [zIndex])
  const [activeThreadId, setActiveThreadId] = useState<string | null>(() => readStoredThreadId(storageKey))
  const [isChatOpen, setIsChatOpen] = useControllableOpen(open, defaultOpen, onOpenChange)
  const [overlayMode, setOverlayMode] = useState<OverlayMode>(() => (
    readStoredThreadId(storageKey) ? null : 'buttons'
  ))
  const [inputValue, setInputValue] = useState('')

  const [remoteConfig, setRemoteConfig] = useState<HomepagePromptsConfig | null>(null)
  const [promptsLoading, setPromptsLoading] = useState(false)

  useEffect(() => {
    if (promptsApiUrl === null) {
      setRemoteConfig(null)
      setPromptsLoading(false)
      return
    }
    let cancelled = false
    setPromptsLoading(true)
    fetchHomepagePrompts({ url: promptsApiUrl || undefined })
      .then((cfg) => {
        if (!cancelled) setRemoteConfig(cfg)
      })
      .catch(() => {
        // fall back to props / built-in defaults
      })
      .finally(() => {
        if (!cancelled) setPromptsLoading(false)
      })
    return () => { cancelled = true }
  }, [promptsApiUrl])

  const greeting = remoteConfig?.greeting || greetingProp
  const placeholder = remoteConfig?.placeholder || placeholderProp
  const prompts = remoteConfig?.prompts?.length ? remoteConfig.prompts : promptsProp
  const infoText = remoteConfig?.info_text || ''

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
      persistThreadId(threadId, storageKey)
      if (threadId === null) {
        setOverlayMode('buttons')
        setInputValue('')
        return
      }
      setOverlayMode(null)
    },
    entities: {
      onClick: (entity) => {
        const slug = typeof entity.data?.slug === 'string' ? entity.data.slug : undefined
        const pageUrl = typeof entity.data?.pageUrl === 'string' ? entity.data.pageUrl : undefined

        if (slug) {
          try {
            const url = new URL(slug, window.location.origin)
            onEntityNavigate?.({ url, slug, entity })
            return
          } catch {
            if (isDev) {
              console.warn('[ChatPanel] Invalid entity slug:', slug)
            }
          }
        }

        if (pageUrl) {
          try {
            const url = new URL(pageUrl, window.location.origin)
            if (url.origin === window.location.origin) {
              onEntityNavigate?.({ url, slug: url.pathname, entity })
              return
            }
            window.open(url.toString(), '_blank', 'noopener,noreferrer')
            return
          } catch {
            if (isDev) {
              console.warn('[ChatPanel] Invalid entity pageUrl:', pageUrl)
            }
          }
        }

        if (isDev) {
          console.warn('[ChatPanel] Missing entity navigation data:', entity)
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
    sendUserMessage({ text: text })
  }, [inputValue, sendUserMessage])

  return (
    <div className={clsx('ffrobot-chat-root', rootClassName)} style={rootStyle}>
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
        <div className="chatkit-body" ref={chatkitBodyRef}>
          <ChatKit control={control} />
          {overlayMode && (
            <div className="ck-greeting-overlay">
              {overlayMode === 'buttons' && (
                <>
                  <div className="ck-greeting-center">
                    <p className="ck-greeting-text">{greeting}</p>
                    <div className="ck-greeting-prompts">
                      {promptsLoading ? (
                        <span className="ck-greeting-loading">Loading…</span>
                      ) : (
                        prompts.map((p) => (
                          <button
                            key={p.label}
                            className="ck-greeting-prompt-btn"
                            onClick={() => handlePromptClick(p.prompt)}
                          >
                            {p.label}
                          </button>
                        ))
                      )}
                    </div>
                    {infoText && (
                      <p className="ck-greeting-info-text">{infoText}</p>
                    )}
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
    </div>
  )
}
