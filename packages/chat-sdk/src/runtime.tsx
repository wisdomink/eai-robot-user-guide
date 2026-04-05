import { StrictMode } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import ChatPanel, { type ChatEntityNavigatePayload, type ChatPanelApiConfig } from './ChatPanel'
import { getDefaultChatkitApiUrl, getDefaultHomepagePromptsUrl } from './chatEndpoints'
import type { ChatSdkInitOptions, ChatSdkInstance } from './types'

const DEFAULT_CONTAINER_ID = 'ffrobot-chat-sdk-root'
const DEFAULT_DOMAIN_KEY = import.meta.env.VITE_CHATKIT_DOMAIN_KEY || 'local-dev'

function resolveMountTarget(mountTarget?: HTMLElement | string) {
  if (typeof document === 'undefined') {
    throw new Error('FFRobotChat can only run in a browser environment.')
  }

  if (!mountTarget) {
    return document.body
  }

  if (typeof mountTarget === 'string') {
    const node = document.querySelector<HTMLElement>(mountTarget)
    if (!node) {
      throw new Error(`FFRobotChat mount target not found: ${mountTarget}`)
    }
    return node
  }

  return mountTarget
}

function resolveApiConfig(options: ChatSdkInitOptions): ChatPanelApiConfig {
  if (options.apiUrl) {
    return {
      url: options.apiUrl,
      domainKey: options.domainKey || DEFAULT_DOMAIN_KEY,
    }
  }

  if (options.apiBaseUrl) {
    const url = new URL(options.apiBaseUrl, window.location.href)
    url.pathname = '/api/chatkit'
    url.search = ''
    url.hash = ''
    return {
      url: url.toString(),
      domainKey: options.domainKey || DEFAULT_DOMAIN_KEY,
    }
  }

  return {
    url: getDefaultChatkitApiUrl(),
    domainKey: options.domainKey || DEFAULT_DOMAIN_KEY,
  }
}

function resolvePromptsApiUrl(options: ChatSdkInitOptions) {
  if (options.promptsApiUrl !== undefined) {
    return options.promptsApiUrl
  }

  if (options.apiUrl) {
    const url = new URL(options.apiUrl, window.location.href)
    url.pathname = '/api/get-homepage-prompts'
    url.search = ''
    url.hash = ''
    return url.toString()
  }

  if (options.apiBaseUrl) {
    const url = new URL(options.apiBaseUrl, window.location.href)
    url.pathname = '/api/get-homepage-prompts'
    url.search = ''
    url.hash = ''
    return url.toString()
  }

  return getDefaultHomepagePromptsUrl()
}

function defaultEntityNavigate({ url }: ChatEntityNavigatePayload) {
  if (url.origin === window.location.origin) {
    window.location.assign(url.toString())
    return
  }

  window.open(url.toString(), '_blank', 'noopener,noreferrer')
}

class ChatSdkController implements ChatSdkInstance {
  private config: ChatSdkInitOptions
  private readonly root: Root
  private readonly container: HTMLElement
  private openState: boolean

  constructor(options: ChatSdkInitOptions = {}) {
    this.config = { ...options }
    this.openState = Boolean(options.defaultOpen)

    const mountTarget = resolveMountTarget(options.mountTarget)
    this.container = document.createElement('div')
    this.container.id = options.containerId || DEFAULT_CONTAINER_ID
    mountTarget.appendChild(this.container)

    this.root = createRoot(this.container)
    this.render()
  }

  open = () => {
    this.openState = true
    this.render()
  }

  close = () => {
    this.openState = false
    this.render()
  }

  destroy = () => {
    this.root.unmount()
    this.container.remove()
  }

  update = (options: Partial<ChatSdkInitOptions>) => {
    this.config = { ...this.config, ...options }
    if (options.defaultOpen !== undefined) {
      this.openState = Boolean(options.defaultOpen)
    }
    this.render()
  }

  isOpen = () => this.openState

  getContainer = () => this.container

  private handleOpenChange = (open: boolean) => {
    this.openState = open
    this.config.onOpenChange?.(open)
    this.render()
  }

  private render() {
    const apiConfig = resolveApiConfig(this.config)
    const promptsApiUrl = resolvePromptsApiUrl(this.config)
    const handleEntityNavigate = this.config.onEntityNavigate || defaultEntityNavigate

    this.root.render(
      <StrictMode>
        <ChatPanel
          open={this.openState}
          onOpenChange={this.handleOpenChange}
          onEntityNavigate={handleEntityNavigate}
          apiConfig={apiConfig}
          title={this.config.title}
          placeholder={this.config.placeholder}
          greeting={this.config.greeting}
          prompts={this.config.prompts}
          promptsApiUrl={promptsApiUrl}
          fabLabel={this.config.fabLabel}
          fabAriaLabel={this.config.fabAriaLabel}
          showFab={this.config.showFab}
          buildVersion={this.config.buildVersion}
          storageKey={this.config.storageKey}
          zIndex={this.config.zIndex}
        />
      </StrictMode>,
    )
  }
}

export function createChatSdkController(options: ChatSdkInitOptions = {}) {
  return new ChatSdkController(options)
}
