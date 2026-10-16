export interface AdminUser {
  username: string
  role: 'admin' | 'user'
  enabled: boolean
  created_at: string
  last_login_at: string | null
}

export interface AdminSession {
  user: AdminUser
  expires_at: number
}

export interface LoginLog {
  username: string
  timestamp: string
  ip: string
  success: boolean
}

export interface LoginLogPage {
  logs: LoginLog[]
  after: string | null
}

export const ADMIN_SESSION_EXPIRED = 'admin-session-expired'

export class AdminApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/admin${path}`, {
    ...init, credentials: 'same-origin', cache: 'no-store',
  })
  if (!response.ok) {
    if (response.status === 401 && path !== '/login' && path !== '/me') {
      window.dispatchEvent(new Event(ADMIN_SESSION_EXPIRED))
    }
    const data = await response.json().catch(() => null)
    throw new AdminApiError(typeof data?.detail === 'string' ? data.detail : `请求失败 (${response.status})`, response.status)
  }
  return response.json() as Promise<T>
}

export async function fetchAdminSession(signal?: AbortSignal): Promise<AdminSession | null> {
  try {
    return await request<AdminSession>('/me', { signal })
  } catch (error) {
    if (error instanceof AdminApiError && error.status === 401) return null
    throw error
  }
}

export function loginAdmin(username: string, password: string) {
  return request<AdminSession>('/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }),
  })
}

export function logoutAdmin() {
  return request<{ ok: boolean }>('/logout', { method: 'POST' })
}

export async function fetchAdminUsers(signal?: AbortSignal) {
  return (await request<{ users: AdminUser[] }>('/users', { signal })).users
}

export async function createAdminUser(username: string, password: string) {
  return (await request<{ user: AdminUser }>('/users', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }),
  })).user
}

export async function updateAdminUser(username: string, changes: { password?: string; enabled?: boolean }) {
  return (await request<{ user: AdminUser }>(`/users/${encodeURIComponent(username)}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(changes),
  })).user
}

export function fetchAdminLoginLogs(username: string, after: string | null, signal?: AbortSignal) {
  const query = new URLSearchParams({ limit: '25' })
  if (username) query.set('username', username)
  if (after) query.set('after', after)
  return request<LoginLogPage>(`/login-logs?${query}`, { signal })
}
