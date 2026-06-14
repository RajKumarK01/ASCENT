const BASE = '/api'

const TOKEN_KEY = 'ascent_token'
let _token: string | null = localStorage.getItem(TOKEN_KEY)
export const setToken = (t: string | null) => {
  _token = t
  if (t) localStorage.setItem(TOKEN_KEY, t)
  else localStorage.removeItem(TOKEN_KEY)
}
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
  submitAssessment: (score_pct: number, correct: number, total: number) =>
    request<any>('/employee/assessment/submit', { method: 'POST', body: JSON.stringify({ score_pct, correct, total }) }),
  scheduleCalendar: (weeks: number) =>
    request<{mode:string;events:any[];created?:number;failed?:number;target_user?:string;errors?:string[];ics?:string;filename?:string}>('/employee/calendar/schedule', { method: 'POST', body: JSON.stringify({ weeks }) }),
  insights:    (team?: string) => request<any>(`/manager/insights${team ? `?team=${team}` : ''}`),
  health:      () => request<{status:string;mode:string}>('/health'),
  contributions: () => request<{[date:string]:number}>('/employee/study/contributions'),
  studyCheckin: () => request<{success:boolean;date:string}>('/employee/study/checkin', { method: 'POST', body: JSON.stringify({}) }),
  profile:     () => request<any>('/employee/profile'),
  updateProfile: (body: {path:string;certification?:string}) => request<any>('/employee/profile', { method: 'POST', body: JSON.stringify(body) }),
  completeModule: (moduleId: string) => request<any>(`/employee/study/module/${encodeURIComponent(moduleId)}/complete`, { method: 'POST', body: JSON.stringify({}) }),
  interpretPath: (description: string) => request<{certification:string;cert_title:string;path:string;reasoning:string;skills:string[];recommended_hours:number;available_certifications:string[]}>('/employee/path/interpret', { method: 'POST', body: JSON.stringify({ description }) }),
  youtube:     (q: string) => request<{query:string;videos:{video_id:string;title:string;channel:string;thumbnail_url:string;url:string}[]}>(`/employee/study/youtube?q=${encodeURIComponent(q)}`),
  agents:      () => request<{agents:{name:string;label:string;kind:string;description:string;sample:string}[]}>('/agents'),
  invokeAgent: (name: string, input: string) => request<{agent:string;input:string;reply:string}>(`/agents/${encodeURIComponent(name)}/invoke`, { method: 'POST', body: JSON.stringify({ input }) }),
  post:        <T,>(path: string, body: any) => request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
}
