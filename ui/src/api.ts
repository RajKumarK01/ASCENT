const BASE = '/api'

let _token: string | null = null
export const setToken = (t: string | null) => { _token = t }
export const getToken = () => _token

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (_token) headers['Authorization'] = `Bearer ${_token}`
  const res = await fetch(BASE + path, { ...opts, headers: { ...headers, ...((opts.headers as Record<string,string>) ?? {}) } })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'Request failed')
  }
  return res.json()
}

export const api = {
  login:       (email: string, password: string) =>
    request<{access_token:string;role:string;scope:string;email:string;name:string}>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  me:          () => request<{email:string;name:string;role:string;scope:string}>('/me'),
  plan:        (weeks=4) => request<any>(`/plan?weeks=${weeks}`),
  regenerate:  (weeks: number) => request<any>('/plan/regenerate', { method: 'POST', body: JSON.stringify({ weeks }) }),
  assessment:  () => request<any>('/assessment'),
  insights:    (team?: string) => request<any>(`/manager/insights${team ? `?team=${team}` : ''}`),
  health:      () => request<{status:string;mode:string}>('/health'),
  chat:        (message: string) => request<{message:string;reply:string;result:any;intent:any}>('/chat', { method: 'POST', body: JSON.stringify({ message }) }),
}
