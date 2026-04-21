import type { ChatEntityNavigatePayload, ChatPromptOption } from './ChatPanel'

export interface ChatSdkInitOptions {
  apiUrl?: string
  apiBaseUrl?: string
  domainKey?: string
  promptsApiUrl?: string | null
  hostUrl?: string
  mountTarget?: HTMLElement | string
  containerId?: string
  defaultOpen?: boolean
  title?: string
  placeholder?: string
  greeting?: string
  prompts?: ChatPromptOption[]
  fabLabel?: string
  fabAriaLabel?: string
  showFab?: boolean
  buildVersion?: string
  storageKey?: string
  zIndex?: number
  loadFonts?: boolean
  onEntityNavigate?: (payload: ChatEntityNavigatePayload) => void
  onOpenChange?: (open: boolean) => void
}

export interface ChatSdkInstance {
  open: () => void
  close: () => void
  destroy: () => void
  update: (options: Partial<ChatSdkInitOptions>) => void
  isOpen: () => boolean
  getContainer: () => HTMLElement
}

export interface ChatSdkPublicApi {
  init: (options?: ChatSdkInitOptions) => Promise<ChatSdkInstance>
  open: () => void
  close: () => void
  destroy: () => void
  update: (options: Partial<ChatSdkInitOptions>) => void
  getInstance: () => ChatSdkInstance | null
}
