/**
 * Global type declarations for FFRobotChat SDK (IIFE).
 *
 * The SDK is loaded via `<script src="ffrobot-chat-sdk.js"></script>`.
 * These types mirror packages/chat-sdk/types/global.d.ts and should be kept in sync
 * when the SDK public API changes.
 */

interface FFRobotChatPromptOption {
  label: string
  prompt: string
}

interface FFRobotChatEntityNavigatePayload {
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

interface FFRobotChatInitOptions {
  apiUrl?: string
  apiBaseUrl?: string
  domainKey?: string
  promptsApiUrl?: string | null
  mountTarget?: HTMLElement | string
  containerId?: string
  defaultOpen?: boolean
  title?: string
  placeholder?: string
  greeting?: string
  prompts?: FFRobotChatPromptOption[]
  fabLabel?: string
  fabAriaLabel?: string
  showFab?: boolean
  buildVersion?: string
  storageKey?: string
  zIndex?: number
  loadFonts?: boolean
  onEntityNavigate?: (payload: FFRobotChatEntityNavigatePayload) => void
  onOpenChange?: (open: boolean) => void
}

interface FFRobotChatInstance {
  open: () => void
  close: () => void
  destroy: () => void
  update: (options: Partial<FFRobotChatInitOptions>) => void
  isOpen: () => boolean
  getContainer: () => HTMLElement
}

interface FFRobotChatPublicApi {
  init: (options?: FFRobotChatInitOptions) => Promise<FFRobotChatInstance>
  open: () => void
  close: () => void
  destroy: () => void
  update: (options: Partial<FFRobotChatInitOptions>) => void
  getInstance: () => FFRobotChatInstance | null
}

interface Window {
  FFRobotChat: FFRobotChatPublicApi
}
