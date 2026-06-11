import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [pw, setPw] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const [showCreds, setShowCreds] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setErr(''); setLoading(true)
    try {
      await login(email, pw)
      nav('/')
    } catch (ex: any) {
      setErr(ex.message ?? 'Login failed')
    } finally { setLoading(false) }
  }

  const DEMO = [
    { email: 'emp.morgan@ascent.demo', pw: 'demo-pass-1', label: 'Employee (L-1001, Cloud Eng)' },
    { email: 'emp.alex@ascent.demo',   pw: 'demo-pass-2', label: 'Employee (L-1002, DevOps)' },
    { email: 'mgr.taylor@ascent.demo', pw: 'demo-mgr',    label: 'Manager (TEAM-A)' },
  ]

  return (
    <div className="min-h-screen flex items-center justify-center bg-github-bg p-4">
      <div className="w-full max-w-sm">
        <div className="bg-github-surface rounded-2xl border border-github-border p-8">
          <div className="text-center mb-6">
            <div className="text-3xl font-bold text-github-text mb-1">ASCENT</div>
            <div className="text-sm text-github-muted">Adaptive Skills &amp; Certification Enablement for Teams</div>
            <div className="mt-2 inline-block px-3 py-1 bg-github-yellow/20 border border-github-yellow/50 rounded-full text-xs text-github-yellow">
              Synthetic demonstration environment
            </div>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-github-text mb-1">Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} required
                className="w-full border border-github-border bg-github-bg rounded-xl px-3 py-2 text-sm text-github-text focus:outline-none focus:ring-2 focus:ring-github-blue" />
            </div>
            <div>
              <label className="block text-sm font-medium text-github-text mb-1">Password</label>
              <input type="password" value={pw} onChange={e => setPw(e.target.value)} required
                className="w-full border border-github-border bg-github-bg rounded-xl px-3 py-2 text-sm text-github-text focus:outline-none focus:ring-2 focus:ring-github-blue" />
            </div>
            {err && <div className="text-sm text-github-red bg-github-red/10 rounded-lg px-3 py-2">{err}</div>}
            <button type="submit" disabled={loading}
              className="w-full bg-github-blue hover:bg-github-blue/80 text-github-bg font-medium py-2.5 rounded-xl text-sm transition-colors disabled:opacity-60">
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <div className="mt-4">
            <button onClick={() => setShowCreds(s => !s)}
              className="text-xs text-github-muted hover:text-github-text flex items-center gap-1 mx-auto transition-colors">
              <span className={`transition-transform ${showCreds ? 'rotate-90' : ''}`}>▶</span>
              Demo credentials
            </button>
            {showCreds && (
              <div className="mt-3 space-y-2">
                {DEMO.map(d => (
                  <button key={d.email} onClick={() => { setEmail(d.email); setPw(d.pw) }}
                    className="w-full text-left px-3 py-2 rounded-lg bg-github-border/30 hover:bg-github-border/50 text-xs text-github-text transition-colors">
                    <div className="font-medium">{d.label}</div>
                    <div className="text-github-muted">{d.email}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="text-center mt-4 text-xs text-github-muted">
          You are interacting with an AI system. Synthetic demo data only.
        </div>
      </div>
    </div>
  )
}
