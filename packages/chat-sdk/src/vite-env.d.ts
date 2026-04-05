/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CHAT_SERVICE_ORIGIN?: string
  readonly VITE_CHATKIT_API_URL?: string
  readonly VITE_CHATKIT_DOMAIN_KEY?: string
  readonly VITE_GET_HOMEPAGE_PROMPTS_URL?: string
}

declare const __BUILD_TIME__: string | undefined
