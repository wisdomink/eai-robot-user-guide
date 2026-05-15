/**
 * Global type declarations for FFRobotChat SDK (IIFE).
 *
 * Include this file in your tsconfig to get type support for `window.FFRobotChat`.
 * The SDK is loaded via `<script src="ffrobot-chat-sdk.js"></script>`.
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

interface FFRobotChatVersionInfo {
  sdkVersion: string
  buildVersion: string
  buildTime: string | null
}

interface FFRobotChatInitOptions {
  apiUrl?: string
  apiBaseUrl?: string
  domainKey?: string
  promptsApiUrl?: string | null
  hostUrl?: string
  mountTarget?: HTMLElement | string
  containerId?: string
  defaultOpen?: boolean
  placeholder?: string
  greeting?: string
  prompts?: FFRobotChatPromptOption[]
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
  getVersion: () => FFRobotChatVersionInfo
}

interface Window {
  FFRobotChat: FFRobotChatPublicApi
}
