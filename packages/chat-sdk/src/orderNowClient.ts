export interface OrderNowRule {
  id: string
  label: string
  pattern: string
  target_url: string
  button_label?: string
  enabled: boolean
}

export interface OrderNowConfig {
  default_url: string
  rules: OrderNowRule[]
}

export const DEFAULT_ORDER_NOW_CONFIG: OrderNowConfig = {
  default_url: 'https://shop.ff.com/',
  rules: [],
}

const requests = new Map<string, Promise<OrderNowConfig>>()

function httpUrl(value: string): URL | null {
  try {
    const url = new URL(value)
    return (url.protocol === 'https:' || url.protocol === 'http:') && !url.username && !url.password ? url : null
  } catch {
    return null
  }
}

function normalizeUrl(value: string): string | null {
  const url = httpUrl(value)
  return url ? `${url.origin}${url.pathname.replace(/\/+$/, '')}` : null
}

/** Resolve at click time so SPA navigation needs neither another request nor router hooks. */
export function resolveOrderNowAction(config: OrderNowConfig, hostUrl: string): { url: string; label: string } {
  const fallback = httpUrl(config.default_url)?.href || DEFAULT_ORDER_NOW_CONFIG.default_url
  const current = normalizeUrl(hostUrl)
  if (!current) return { url: fallback, label: 'Order Now' }

  let target = fallback
  let label = 'Order Now'
  let bestRank = -1
  for (const rule of config.rules) {
    if (!rule.enabled || !httpUrl(rule.target_url)) continue
    const isPrefix = rule.pattern.endsWith('/*')
    const pattern = normalizeUrl(isPrefix ? rule.pattern.slice(0, -2) : rule.pattern)
    if (!pattern) continue
    const matches = current === pattern || (isPrefix && current.startsWith(`${pattern}/`))
    // Exact matches always win; among prefixes, the longest path wins.
    const rank = isPrefix ? pattern.length : Infinity
    if (matches && rank > bestRank) {
      bestRank = rank
      target = rule.target_url
      label = rule.button_label?.trim() || 'Order Now'
    }
  }
  return { url: target, label }
}

export function resolveOrderNowUrl(config: OrderNowConfig, hostUrl: string): string {
  return resolveOrderNowAction(config, hostUrl).url
}

/** Cache the request (including failure) for this document, also deduplicating StrictMode mounts. */
export function fetchOrderNowConfig(apiUrl: string): Promise<OrderNowConfig> {
  let request = requests.get(apiUrl)
  if (!request) {
    request = fetch(apiUrl, { cache: 'no-store' })
      .then(async response => {
        if (!response.ok) throw new Error(`Order Now API error (${response.status})`)
        const data = await response.json()
        if (!data || !Array.isArray(data.rules)) throw new Error('Invalid Order Now config')
        return {
          default_url: typeof data.default_url === 'string' && httpUrl(data.default_url)
            ? data.default_url : DEFAULT_ORDER_NOW_CONFIG.default_url,
          rules: data.rules.filter((rule: unknown): rule is OrderNowRule => {
            if (!rule || typeof rule !== 'object') return false
            const item = rule as Partial<OrderNowRule>
            return typeof item.id === 'string' && typeof item.label === 'string'
              && typeof item.pattern === 'string' && typeof item.target_url === 'string'
              && (item.button_label === undefined || typeof item.button_label === 'string')
              && item.enabled === true && httpUrl(item.target_url) !== null
          }),
        }
      })
      .catch(() => DEFAULT_ORDER_NOW_CONFIG)
    requests.set(apiUrl, request)
  }
  return request
}
