export interface HomepagePrompt {
  id: string
  enabled: boolean
  label: string
  prompt: string
  sort_order: number
}

export type HomepagePromptPayload = Omit<HomepagePrompt, 'id'> & { id?: string }

export interface HomepagePromptsConfig {
  greeting: string
  placeholder: string
  info_text: string
  prompts: HomepagePrompt[]
}

export interface HomepageSettings {
  greeting: string
  placeholder: string
  info_text: string
}

export interface FetchHomepagePromptsOptions {
  all?: boolean
  url?: string
}

const LOCAL_CHAT_SERVICE_ORIGIN = 'http://127.0.0.1:8000'

function getChatServiceOrigin() {
  const configured = import.meta.env.VITE_CHAT_SERVICE_ORIGIN?.trim()
  return configured ? configured.replace(/\/$/, '') : LOCAL_CHAT_SERVICE_ORIGIN
}

function getHomepagePromptsUrl() {
  return import.meta.env.VITE_GET_HOMEPAGE_PROMPTS_URL || `${getChatServiceOrigin()}/api/get-homepage-prompts`
}

const SAVE_HOMEPAGE_PROMPT_URL =
  import.meta.env.VITE_SAVE_HOMEPAGE_PROMPT_URL || '/api/save-homepage-prompt'
const DELETE_HOMEPAGE_PROMPT_URL =
  import.meta.env.VITE_DELETE_HOMEPAGE_PROMPT_URL || '/api/delete-homepage-prompt'
const SAVE_HOMEPAGE_SETTINGS_URL =
  import.meta.env.VITE_SAVE_HOMEPAGE_SETTINGS_URL || '/api/save-homepage-settings'

export async function fetchHomepagePrompts(
  options: boolean | FetchHomepagePromptsOptions = false,
): Promise<HomepagePromptsConfig> {
  const normalized = typeof options === 'boolean' ? { all: options } : options
  const baseUrl = normalized.url ?? getHomepagePromptsUrl()
  const url = normalized.all ? `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}all=true` : baseUrl
  const res = await fetch(url)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Homepage prompts API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return {
    greeting: data.greeting ?? '',
    placeholder: data.placeholder ?? '',
    info_text: data.info_text ?? '',
    prompts: (data.prompts || []) as HomepagePrompt[],
  }
}

export async function saveHomepagePrompt(
  payload: HomepagePromptPayload & { id?: string },
): Promise<{ prompt: HomepagePrompt; created: boolean }> {
  const res = await fetch(SAVE_HOMEPAGE_PROMPT_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Homepage prompts API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return {
    prompt: data.prompt as HomepagePrompt,
    created: Boolean(data.created),
  }
}

export async function deleteHomepagePrompt(id: string): Promise<HomepagePrompt> {
  const res = await fetch(`${DELETE_HOMEPAGE_PROMPT_URL}/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Homepage prompts API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return data.prompt as HomepagePrompt
}

export async function saveHomepageSettings(
  settings: Partial<HomepageSettings>,
): Promise<HomepageSettings> {
  const res = await fetch(SAVE_HOMEPAGE_SETTINGS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Homepage settings API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return data.settings as HomepageSettings
}
