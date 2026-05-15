/**
 * @ffrobot/chat-sdk — ChatPanel UI、端点解析与可选的浏览器嵌入 SDK（见 `@ffrobot/chat-sdk/embed`）。
 */
export { default as ChatPanel } from './ChatPanel'
export type {
  ChatPanelProps,
  ChatPromptOption,
  ChatPanelApiConfig,
  ChatEntityNavigatePayload,
} from './ChatPanel'

export {
  getDefaultChatServiceOrigin,
  getDefaultChatkitApiUrl,
  getDefaultHomepagePromptsUrl,
} from './chatEndpoints'

export {
  fetchHomepagePrompts,
  type HomepagePrompt,
  type HomepagePromptsConfig,
  type FetchHomepagePromptsOptions,
} from './homepagePromptsClient'

export { createChatSdkController } from './runtime'

export {
  getChatSdkVersionInfo,
  type ChatSdkVersionInfo,
} from './version'

export type {
  ChatSdkInitOptions,
  ChatSdkInstance,
  ChatSdkPublicApi,
} from './types'
