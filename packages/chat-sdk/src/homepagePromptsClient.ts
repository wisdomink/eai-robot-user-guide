import { getDefaultHomepagePromptsUrl } from './chatEndpoints'

export interface HomepagePrompt {
  id: string
  enabled: boolean
  label: string
  prompt: string
  sort_order: number
}

export interface HomepagePromptsConfig {
  id?: string
  pattern?: string
  label?: string
  greeting: string
  placeholder: string
  info_text: string
  prompts: HomepagePrompt[]
}

export interface FetchHomepagePromptsOptions {
  all?: boolean
  url?: string
  hostUrl?: string
}

function getHomepagePromptsUrl() {
  return import.meta.env.VITE_GET_HOMEPAGE_PROMPTS_URL || getDefaultHomepagePromptsUrl()
}

export async function fetchHomepagePrompts(
  options: boolean | FetchHomepagePromptsOptions = false,
): Promise<HomepagePromptsConfig> {
  const normalized = typeof options === 'boolean' ? { all: options } : options
  const baseUrl = normalized.url || getHomepagePromptsUrl()
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
    prompts: (data.prompts || []) as HomepagePrompt[],
  }
}
