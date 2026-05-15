import {
  useState,
  useCallback,
  useEffect,
  useRef,
  useMemo,
  type CSSProperties,
  type FormEvent,
  type RefObject,
} from 'react'
import { ChatKit, useChatKit } from '@openai/chatkit-react'
import clsx from 'clsx'
import { fetchHomepagePrompts, type HomepagePromptsConfig } from './homepagePromptsClient'
import { getDefaultChatkitApiUrl } from './chatEndpoints'
import { getChatSdkVersionInfo } from './version'

const isDev = Boolean(typeof import.meta !== 'undefined' && import.meta.env?.DEV)

const CHATKIT_THREAD_STORAGE_KEY = 'ffrobot:chatkit:thread-id'
const CHATKIT_DOMAIN_KEY = import.meta.env.VITE_CHATKIT_DOMAIN_KEY || 'local-dev'
const VERSION_CLICK_THRESHOLD = 5
const VERSION_CLICK_WINDOW_MS = 2000

function resolveChatKitApiUrl() {
  const raw = import.meta.env.VITE_CHATKIT_API_URL
  if (!raw) return getDefaultChatkitApiUrl()
  if (/^https?:\/\//.test(raw)) {
    return raw
  }
  return new URL(raw, window.location.origin).toString()
}

function buildApiConfig(): ChatPanelApiConfig {
  return {
    url: resolveChatKitApiUrl(),
    domainKey: CHATKIT_DOMAIN_KEY,
  }
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

const FALLBACK_GREETING = "Do you want to know about FF's products?"
const FALLBACK_PLACEHOLDER = 'Ask anything about FF...'
const CHAT_PANEL_HEADER_TITLE = 'FF Assist'
const CHAT_FAB_LABEL = 'FF Assist'
const HOMEPAGE_DISCLAIMER = 'FF Assist uses AI, mistakes may occur.'
const FALLBACK_PROMPTS = [
  { label: 'How can I buy an FF robot?', prompt: 'How can I buy an FF robot?' },
  { label: 'When will FF robots be delivered?', prompt: 'When will FF robots be delivered?' },
  { label: 'What product lines does FF currently offer?', prompt: 'What product lines does FF currently offer?' },
]

type OverlayMode = 'buttons' | null

export interface ChatPromptOption {
  label: string
  prompt: string
}

export interface ChatPanelApiConfig {
  url: string
  domainKey: string
  fetch?: typeof fetch
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
  placeholder?: string
  greeting?: string
  prompts?: ChatPromptOption[]
  promptsApiUrl?: string | null
  hostUrl?: string
  fabAriaLabel?: string
  showFab?: boolean
  buildVersion?: string
  storageKey?: string
  zIndex?: number
  rootClassName?: string
  loadChatKitRuntime?: () => Promise<void>
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

const SOURCE_HEADING_RE = /^Sources$/i

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

function useSourceSectionHider(containerRef: RefObject<HTMLDivElement | null>) {
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

function useScrollBleedBlocker<T extends HTMLElement>(containerRef: RefObject<T | null>, active: boolean) {
  useEffect(() => {
    if (!active) return
    const container = containerRef.current
    if (!container) return

    const blockScroll = (event: Event) => {
      event.preventDefault()
      event.stopPropagation()
    }

    container.addEventListener('wheel', blockScroll, { passive: false })
    container.addEventListener('touchmove', blockScroll, { passive: false })

    return () => {
      container.removeEventListener('wheel', blockScroll)
      container.removeEventListener('touchmove', blockScroll)
    }
  }, [active, containerRef])
}

export default function ChatPanel({
  open,
  defaultOpen = false,
  onOpenChange,
  onEntityNavigate,
  apiConfig,
  panelId = 'chatPanel',
  className,
  placeholder: placeholderProp = FALLBACK_PLACEHOLDER,
  greeting: greetingProp = FALLBACK_GREETING,
  prompts: promptsProp = FALLBACK_PROMPTS,
  promptsApiUrl,
  hostUrl,
  fabAriaLabel = 'Open FF Assist',
  showFab = true,
  buildVersion = getChatSdkVersionInfo().buildVersion,
  storageKey = CHATKIT_THREAD_STORAGE_KEY,
  zIndex,
  rootClassName,
  loadChatKitRuntime,
}: ChatPanelProps) {
  const chatkitBodyRef = useRef<HTMLDivElement>(null)
  const versionClickCountRef = useRef(0)
  const versionClickResetTimerRef = useRef<number | null>(null)
  useSourceSectionHider(chatkitBodyRef)

  const resolvedApiConfig = useMemo(() => {
    const base = apiConfig ?? buildApiConfig()
    const baseFetch = base.fetch ?? globalThis.fetch.bind(globalThis)
    const contextualFetch: typeof fetch = (input, init) => {
      const headers = new Headers(init?.headers)
      const currentUrl = hostUrl || (typeof window !== 'undefined' ? window.location.href : '')
      if (currentUrl) {
        headers.set('x-ff-page-url', currentUrl)
      }
      return baseFetch(input, init ? { ...init, headers } : { headers })
    }
    return { ...base, fetch: contextualFetch }
  }, [apiConfig, hostUrl])
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
  const [newChatConfirmOpen, setNewChatConfirmOpen] = useState(false)
  const [versionDialogOpen, setVersionDialogOpen] = useState(false)
  const isRespondingRef = useRef(false)
  const isMountedRef = useRef(true)
  const chatKitRuntimePromiseRef = useRef<Promise<void> | null>(null)
  const [chatKitRuntimeStatus, setChatKitRuntimeStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>(
    () => (loadChatKitRuntime ? 'idle' : 'ready'),
  )
  const [chatKitRuntimeError, setChatKitRuntimeError] = useState<unknown>(null)

  const [remoteConfig, setRemoteConfig] = useState<HomepagePromptsConfig | null>(null)
  const [promptsLoading, setPromptsLoading] = useState(false)
  useScrollBleedBlocker(
    chatkitBodyRef,
    isChatOpen && (chatKitRuntimeStatus !== 'ready' || overlayMode === 'buttons'),
  )

  useEffect(() => {
    return () => {
      isMountedRef.current = false
    }
  }, [])

  useEffect(() => {
    return () => {
      if (versionClickResetTimerRef.current !== null) {
        window.clearTimeout(versionClickResetTimerRef.current)
      }
    }
  }, [])

  useEffect(() => {
    chatKitRuntimePromiseRef.current = null
    setChatKitRuntimeError(null)
    setChatKitRuntimeStatus(loadChatKitRuntime ? 'idle' : 'ready')
  }, [loadChatKitRuntime])

  useEffect(() => {
    if (!isChatOpen || !loadChatKitRuntime || chatKitRuntimeStatus !== 'idle') {
      return
    }

    setChatKitRuntimeStatus('loading')
    setChatKitRuntimeError(null)

    const promise = chatKitRuntimePromiseRef.current ?? loadChatKitRuntime()
    chatKitRuntimePromiseRef.current = promise

    promise
      .then(() => {
        if (!isMountedRef.current) return
        setChatKitRuntimeStatus('ready')
      })
      .catch((error) => {
        chatKitRuntimePromiseRef.current = null
        if (!isMountedRef.current) return
        setChatKitRuntimeError(error)
        setChatKitRuntimeStatus('error')
      })
  }, [chatKitRuntimeStatus, isChatOpen, loadChatKitRuntime])

  useEffect(() => {
    if (promptsApiUrl === null) {
      setRemoteConfig(null)
      setPromptsLoading(false)
      return
    }
    if (!isChatOpen || overlayMode !== 'buttons') {
      setPromptsLoading(false)
      return
    }

    let cancelled = false
    setRemoteConfig(null)
    setPromptsLoading(true)
    fetchHomepagePrompts({
      url: promptsApiUrl || undefined,
      hostUrl: hostUrl || window.location.href,
    })
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
  }, [hostUrl, isChatOpen, overlayMode, promptsApiUrl])

  const greeting = remoteConfig?.greeting || greetingProp
  const placeholder = remoteConfig?.placeholder || placeholderProp
  const prompts = remoteConfig?.prompts?.length ? remoteConfig.prompts : promptsProp
  const infoText = remoteConfig?.info_text || ''
  const versionInfo = useMemo(() => ({
    ...getChatSdkVersionInfo(),
    buildVersion,
  }), [buildVersion])

  const openChat = useCallback(() => {
    setIsChatOpen(true)
  }, [setIsChatOpen])

  const closeChat = useCallback(() => {
    setIsChatOpen(false)
  }, [setIsChatOpen])

  const retryChatKitRuntime = useCallback(() => {
    chatKitRuntimePromiseRef.current = null
    setChatKitRuntimeError(null)
    setChatKitRuntimeStatus('idle')
  }, [])

  const { sendUserMessage, setThreadId, control } = useChatKit({
    locale: 'en',
    api: resolvedApiConfig,
    initialThread: activeThreadId,
    header: {
      enabled: false,
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
      isRespondingRef.current = true
    },
    onResponseEnd: () => {
      isRespondingRef.current = false
    },
    onThreadChange: ({ threadId }: { threadId: string | null }) => {
      setActiveThreadId(threadId)
      persistThreadId(threadId, storageKey)
      isRespondingRef.current = false
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
      radius: 'soft',
    },
  })

  const handleNewChat = useCallback(() => {
    if (!activeThreadId) {
      setThreadId(null)
      return
    }
    setNewChatConfirmOpen(true)
  }, [activeThreadId, setThreadId])

  const handleConfirmNewChat = useCallback(() => {
    setNewChatConfirmOpen(false)
    const wasResponding = isRespondingRef.current
    isRespondingRef.current = false
    if (isDev && wasResponding) {
      console.info('[ChatPanel] Starting new chat while old response was in-flight; aborting via setThreadId(null).')
    }
    setThreadId(null)
  }, [setThreadId])

  const handleCancelNewChat = useCallback(() => {
    setNewChatConfirmOpen(false)
  }, [])

  const resetVersionClickCounter = useCallback(() => {
    versionClickCountRef.current = 0
    if (versionClickResetTimerRef.current !== null) {
      window.clearTimeout(versionClickResetTimerRef.current)
      versionClickResetTimerRef.current = null
    }
  }, [])

  const handleHeaderTitleClick = useCallback(() => {
    versionClickCountRef.current += 1
    if (versionClickCountRef.current >= VERSION_CLICK_THRESHOLD) {
      resetVersionClickCounter()
      setVersionDialogOpen(true)
      return
    }

    if (versionClickResetTimerRef.current !== null) {
      window.clearTimeout(versionClickResetTimerRef.current)
    }
    versionClickResetTimerRef.current = window.setTimeout(() => {
      versionClickCountRef.current = 0
      versionClickResetTimerRef.current = null
    }, VERSION_CLICK_WINDOW_MS)
  }, [resetVersionClickCounter])

  const closeVersionDialog = useCallback(() => {
    setVersionDialogOpen(false)
  }, [])

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
    <div
      className={clsx('ffrobot-chat-root', rootClassName)}
      style={rootStyle}
      data-sdk-version={versionInfo.sdkVersion}
      data-build-version={versionInfo.buildVersion}
      data-build-time={versionInfo.buildTime || undefined}
    >
      {showFab && !isChatOpen && (
        <button
          type="button"
          className="chat-fab"
          onClick={openChat}
          aria-label={fabAriaLabel}
          aria-controls={panelId}
          aria-expanded={false}
        >
          <span className="chat-fab-backdrop" aria-hidden="true" />
          <span className="chat-fab-content">
            <span className="chat-fab-icon" aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M12 11H12.01M16 11H16.01M8 11H8.01M22 17C22 17.5304 21.7893 18.0391 21.4142 18.4142C21.0391 18.7893 20.5304 19 20 19H6.828C6.29761 19.0001 5.78899 19.2109 5.414 19.586L3.212 21.788C3.1127 21.8873 2.9862 21.9549 2.84849 21.9823C2.71077 22.0097 2.56803 21.9956 2.43831 21.9419C2.30858 21.8881 2.1977 21.7971 2.11969 21.6804C2.04167 21.5637 2.00002 21.4264 2 21.286V5C2 4.46957 2.21071 3.96086 2.58579 3.58579C2.96086 3.21071 3.46957 3 4 3H20C20.5304 3 21.0391 3.21071 21.4142 3.58579C21.7893 3.96086 22 4.46957 22 5V17Z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
            <span className="chat-fab-label">{CHAT_FAB_LABEL}</span>
          </span>
        </button>
      )}

      {isChatOpen && (
        <div
          className={clsx('chat-panel', 'open', className)}
          id={panelId}
          aria-hidden={false}
        >
          <div className="chat-panel-header">
            <button
              type="button"
              className="chat-panel-header-btn"
              onClick={handleNewChat}
              aria-label="New chat"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path
                  d="M20 4H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h3v4l4-4h9a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2Z"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinejoin="round"
                />
                <path d="M12 8v6M9 11h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
              </svg>
            </button>
            <span
              className="chat-panel-header-title"
              onClick={handleHeaderTitleClick}
            >
              {CHAT_PANEL_HEADER_TITLE}
            </span>
            <button
              type="button"
              className="chat-panel-header-btn"
              onClick={closeChat}
              aria-label="Minimize"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path
                  d="M5 12h14"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                />
              </svg>
            </button>
          </div>
          <div className="chatkit-body" ref={chatkitBodyRef}>
            {chatKitRuntimeStatus === 'ready' ? (
              <ChatKit control={control} />
            ) : (
              <div className="chat-panel-runtime-state" role="status" aria-live="polite">
                {chatKitRuntimeStatus === 'error' ? (
                  <>
                    <p className="chat-panel-runtime-title">FF Assist could not load.</p>
                    <button
                      type="button"
                      className="chat-panel-runtime-action"
                      onClick={retryChatKitRuntime}
                    >
                      Retry
                    </button>
                    {isDev && chatKitRuntimeError instanceof Error && (
                      <p className="chat-panel-runtime-debug">{chatKitRuntimeError.message}</p>
                    )}
                  </>
                ) : (
                  <p className="chat-panel-runtime-title">Loading FF Assist...</p>
                )}
              </div>
            )}
            {chatKitRuntimeStatus === 'ready' && overlayMode && (
              <div className="ck-greeting-overlay">
                {overlayMode === 'buttons' && (
                  <>
                    <div className="ck-greeting-center">
                      <p className="ck-greeting-text">{greeting}</p>
                      {infoText && (
                        <p className="ck-greeting-info-text">{infoText}</p>
                      )}
                    </div>
                    <div className="ck-greeting-bottom">
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
                      <p className="ck-greeting-disclaimer">{HOMEPAGE_DISCLAIMER}</p>
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
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
          {newChatConfirmOpen && (
            <div
              className="chat-panel-confirm-backdrop"
              role="presentation"
              onClick={handleCancelNewChat}
            >
              <div
                className="chat-panel-confirm-dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby="chat-panel-confirm-title"
                onClick={(e) => e.stopPropagation()}
              >
                <h3 id="chat-panel-confirm-title" className="chat-panel-confirm-title">
                  Start a new chat?
                </h3>
                <p className="chat-panel-confirm-body">
                  This will clear out your current chat history and start a fresh conversation.
                </p>
                <div className="chat-panel-confirm-actions">
                  <button
                    type="button"
                    className="chat-panel-confirm-btn chat-panel-confirm-btn-secondary"
                    onClick={handleCancelNewChat}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="chat-panel-confirm-btn chat-panel-confirm-btn-primary"
                    onClick={handleConfirmNewChat}
                    autoFocus
                  >
                    OK
                  </button>
                </div>
              </div>
            </div>
          )}
          {versionDialogOpen && (
            <div
              className="chat-panel-version-backdrop"
              role="presentation"
              onClick={closeVersionDialog}
            >
              <div
                className="chat-panel-version-dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby="chat-panel-version-title"
                onClick={(e) => e.stopPropagation()}
              >
                <h3 id="chat-panel-version-title" className="chat-panel-version-title">
                  FF Assist
                </h3>
                <dl className="chat-panel-version-list">
                  <div className="chat-panel-version-row">
                    <dt>SDK version</dt>
                    <dd>{versionInfo.sdkVersion}</dd>
                  </div>
                  <div className="chat-panel-version-row">
                    <dt>Build version</dt>
                    <dd>{versionInfo.buildVersion}</dd>
                  </div>
                  <div className="chat-panel-version-row">
                    <dt>Build time</dt>
                    <dd>{versionInfo.buildTime || 'Unavailable'}</dd>
                  </div>
                </dl>
                <button
                  type="button"
                  className="chat-panel-version-close"
                  onClick={closeVersionDialog}
                  autoFocus
                >
                  OK
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
