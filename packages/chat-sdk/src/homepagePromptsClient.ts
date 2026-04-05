import { getDefaultHomepagePromptsUrl } from './chatEndpoints'

export interface HomepagePrompt {
  id: string
  enabled: boolean
  label: string
  prompt: string
  sort_order: number
}

export interface HomepagePromptsConfig {
  greeting: string
  placeholder: string
  prompts: HomepagePrompt[]
}

export interface FetchHomepagePromptsOptions {
  all?: boolean
  url?: string
}

function getHomepagePromptsUrl() {
  return import.meta.env.VITE_GET_HOMEPAGE_PROMPTS_URL || getDefaultHomepagePromptsUrl()
}

export async function fetchHomepagePrompts(
  options: boolean | FetchHomepagePromptsOptions = false,
): Promise<HomepagePromptsConfig> {
  const normalized = typeof options === 'boolean' ? { all: options } : options
  const baseUrl = normalized.url || getHomepagePromptsUrl()
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
    prompts: (data.prompts || []) as HomepagePrompt[],
  }
}
