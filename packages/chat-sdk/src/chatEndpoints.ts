const LOCAL_CHAT_SERVICE_ORIGIN = 'http://127.0.0.1:8000'

export function getDefaultChatServiceOrigin() {
  const configured = import.meta.env.VITE_CHAT_SERVICE_ORIGIN?.trim()
  return configured ? configured.replace(/\/$/, '') : LOCAL_CHAT_SERVICE_ORIGIN
}

export function getDefaultChatkitApiUrl() {
  return `${getDefaultChatServiceOrigin()}/api/chatkit`
}

export function getDefaultHomepagePromptsUrl() {
  return `${getDefaultChatServiceOrigin()}/api/get-homepage-prompts`
}
