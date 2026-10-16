export interface OrderNowRule {
  id: string
  label: string
  pattern: string
  target_url: string
  button_label: string
  enabled: boolean
}

export type OrderNowRulePayload = Omit<OrderNowRule, 'id'> & { id?: string }

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { ...init, cache: 'no-store' })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : `请求失败 (${response.status})`)
  }
  return data as T
}

export function fetchOrderNowRules() {
  return request<{ default_url: string; rules: OrderNowRule[] }>('/api/get-order-now-config?all=true')
}

export function saveOrderNowRule(rule: OrderNowRulePayload) {
  return request<{ rule: OrderNowRule; created: boolean }>('/api/save-order-now-rule', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rule),
  })
}

export function deleteOrderNowRule(id: string) {
  return request<{ rule: OrderNowRule }>(`/api/delete-order-now-rule/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  })
}
