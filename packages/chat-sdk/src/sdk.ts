import chatPanelCssText from './chat-panel.css?inline'
import { GOOGLE_FONTS_ID, GOOGLE_FONTS_URL } from './chatFonts'
import { createChatSdkController } from './runtime'
import { getChatSdkVersionInfo } from './version'
import type { ChatSdkInitOptions, ChatSdkInstance, ChatSdkPublicApi } from './types'

const CHATKIT_SCRIPT_ID = 'ffrobot-chatkit-script'
const CHATKIT_SCRIPT_URL = 'https://cdn.platform.openai.com/deployments/chatkit/chatkit.js'
const CHAT_STYLE_ID = 'ffrobot-chat-sdk-style'

let activeInstance: ChatSdkInstance | null = null
let chatKitScriptPromise: Promise<void> | null = null

type RandomUuidFunction = () => `${string}-${string}-${string}-${string}-${string}`

function ensureBrowser() {
  if (typeof window === 'undefined' || typeof document === 'undefined') {
    throw new Error('FFRobotChat can only run in a browser environment.')
  }
}

function ensureRandomUuid() {
  const cryptoObject = typeof globalThis === 'undefined'
    ? undefined
    : globalThis.crypto as (Crypto & { randomUUID?: RandomUuidFunction }) | undefined

  if (!cryptoObject || typeof cryptoObject.randomUUID === 'function') {
    return
  }

  cryptoObject.randomUUID = function randomUUID() {
    return '10000000-1000-4000-8000-100000000000'.replace(/[018]/g, (char) => {
      return (Number(char) ^ cryptoObject.getRandomValues(new Uint8Array(1))[0] & 15 >> Number(char) / 4).toString(16)
    }) as ReturnType<RandomUuidFunction>
  }
}

function ensureStyles() {
  if (document.getElementById(CHAT_STYLE_ID)) {
    return
  }

  const style = document.createElement('style')
  style.id = CHAT_STYLE_ID
  style.textContent = chatPanelCssText
  document.head.appendChild(style)
}

function ensureFonts() {
  if (document.getElementById(GOOGLE_FONTS_ID)) {
    return
  }

  const link = document.createElement('link')
  link.id = GOOGLE_FONTS_ID
  link.rel = 'stylesheet'
  link.href = GOOGLE_FONTS_URL
  document.head.appendChild(link)
}

/** Avoid FAB/header FOUT: first paint used system sans, then Roboto swaps in and looks heavier. */
async function waitForRobotoTextFonts(): Promise<void> {
  if (typeof document === 'undefined' || !document.fonts?.load) {
    return
  }
  const timeoutMs = 3000
  const deadline = new Promise<void>((resolve) => {
    window.setTimeout(resolve, timeoutMs)
  })
  const load = document.fonts.load('400 15px Roboto').catch(() => undefined)
  await Promise.race([load, deadline])
}

function ensureChatKitScript() {
  if (chatKitScriptPromise) {
    return chatKitScriptPromise
  }

  const existing = document.getElementById(CHATKIT_SCRIPT_ID) as HTMLScriptElement | null
  if (existing?.dataset.loaded === 'true') {
    chatKitScriptPromise = Promise.resolve()
    return chatKitScriptPromise
  }

  chatKitScriptPromise = new Promise((resolve, reject) => {
    const script = existing || document.createElement('script')

    script.id = CHATKIT_SCRIPT_ID
    script.src = CHATKIT_SCRIPT_URL
    script.async = true

    script.addEventListener('load', () => {
      script.dataset.loaded = 'true'
      resolve()
    }, { once: true })

    script.addEventListener('error', () => {
      chatKitScriptPromise = null
      reject(new Error(`Failed to load ChatKit runtime from ${CHATKIT_SCRIPT_URL}`))
    }, { once: true })

    if (!existing) {
      document.head.appendChild(script)
    }
  })

  return chatKitScriptPromise
}

async function init(options: ChatSdkInitOptions = {}) {
  ensureBrowser()
  ensureRandomUuid()
  ensureStyles()
  if (options.loadFonts !== false) {
    ensureFonts()
  }
  if (options.loadFonts !== false) {
    await waitForRobotoTextFonts()
  }

  if (activeInstance) {
    activeInstance.update(options)
    return activeInstance
  }

  activeInstance = createChatSdkController(options, {
    loadChatKitRuntime: ensureChatKitScript,
  })
  return activeInstance
}

function open() {
  activeInstance?.open()
}

function close() {
  activeInstance?.close()
}

function destroy() {
  activeInstance?.destroy()
  activeInstance = null
}

function update(options: Partial<ChatSdkInitOptions>) {
  activeInstance?.update(options)
}

function getInstance() {
  return activeInstance
}

const FFRobotChat: ChatSdkPublicApi = {
  init,
  open,
  close,
  destroy,
  update,
  getInstance,
  getVersion: getChatSdkVersionInfo,
}

declare global {
  interface Window {
    FFRobotChat: ChatSdkPublicApi
  }
}

if (typeof window !== 'undefined') {
  window.FFRobotChat = FFRobotChat
}

export default FFRobotChat
export type { ChatSdkInitOptions, ChatSdkInstance, ChatSdkPublicApi } from './types'
export type { ChatSdkVersionInfo } from './version'
