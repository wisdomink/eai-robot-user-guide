export type HomepagePromptType = 'message' | 'lead_capture'

export interface HomepagePrompt {
  id: string
  enabled: boolean
  type: HomepagePromptType
  label: string
  prompt: string
  reply_text: string
  sort_order: number
}

export interface HomepagePage {
  id: string
  pattern: string
  label: string
  greeting: string
  placeholder: string
  info_text: string
  prompts: HomepagePrompt[]
}

export type HomepagePromptPayload = Omit<HomepagePrompt, 'id'> & { id?: string }
export type HomepagePagePayload = Omit<HomepagePage, 'id' | 'prompts'> & {
  id?: string
  prompts: HomepagePromptPayload[]
}

export interface HomepagePromptsConfig {
  id?: string
  pattern?: string
  label?: string
  greeting: string
  placeholder: string
  info_text: string
  global_prompts: HomepagePrompt[]
  prompts: HomepagePrompt[]
}

export interface FetchHomepagePromptsOptions {
  all?: boolean
  url?: string
  hostUrl?: string
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
  import.meta.env.VITE_SAVE_HOMEPAGE_PAGE_URL || '/api/save-homepage-page'
const DELETE_HOMEPAGE_PROMPT_URL =
  import.meta.env.VITE_DELETE_HOMEPAGE_PAGE_URL || '/api/delete-homepage-page'
const SAVE_HOMEPAGE_GLOBAL_PROMPTS_URL =
  import.meta.env.VITE_SAVE_HOMEPAGE_GLOBAL_PROMPTS_URL || '/api/save-homepage-global-prompts'

export async function fetchHomepagePrompts(
  options: boolean | FetchHomepagePromptsOptions = false,
): Promise<HomepagePromptsConfig> {
  const normalized = typeof options === 'boolean' ? { all: options } : options
  const baseUrl = normalized.url ?? getHomepagePromptsUrl()
  const requestUrl = new URL(baseUrl, window.location.href)
  if (normalized.all) {
    requestUrl.searchParams.set('all', 'true')
  }
  if (normalized.hostUrl) {
    requestUrl.searchParams.set('url', normalized.hostUrl)
  }
  const res = await fetch(requestUrl.toString())
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Homepage prompts API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return {
    id: data.id ?? '',
    pattern: data.pattern ?? '',
    label: data.label ?? '',
    greeting: data.greeting ?? '',
    placeholder: data.placeholder ?? '',
    info_text: data.info_text ?? '',
    global_prompts: (data.global_prompts || []) as HomepagePrompt[],
    prompts: (data.prompts || []) as HomepagePrompt[],
  }
}

export async function fetchAllHomepagePages(): Promise<{ pages: HomepagePage[]; global_prompts: HomepagePrompt[] }> {
  const requestUrl = new URL(getHomepagePromptsUrl(), window.location.href)
  requestUrl.searchParams.set('all', 'true')
  const res = await fetch(requestUrl.toString())
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Homepage pages API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return {
    pages: (data.pages || []) as HomepagePage[],
    global_prompts: (data.global_prompts || []) as HomepagePrompt[],
  }
}

export async function saveHomepageGlobalPrompts(
  prompts: HomepagePromptPayload[],
): Promise<HomepagePrompt[]> {
  const res = await fetch(SAVE_HOMEPAGE_GLOBAL_PROMPTS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ global_prompts: prompts }),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Save global prompts API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return data.global_prompts as HomepagePrompt[]
}

export async function saveHomepagePage(
  payload: HomepagePagePayload,
): Promise<{ page: HomepagePage; created: boolean }> {
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
    page: data.page as HomepagePage,
    created: Boolean(data.created),
  }
}

export async function deleteHomepagePage(id: string): Promise<HomepagePage> {
  const res = await fetch(`${DELETE_HOMEPAGE_PROMPT_URL}/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Homepage prompts API error (${res.status}): ${text}`)
  }
  const data = await res.json()
  return data.page as HomepagePage
}
