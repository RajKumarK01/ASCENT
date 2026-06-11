import { useState, type FormEvent } from 'react'
import { api } from '../api'
import { Badge } from './Badge'

interface PathSetupModalProps {
  profile: any
  onConfirm: (path: string, certification: string) => Promise<void>
  onDismiss: () => void
}

type Tab = 'recommended' | 'describe'

export function PathSetupModal({ profile, onConfirm, onDismiss }: PathSetupModalProps) {
  const [tab, setTab] = useState<Tab>('recommended')
  const [description, setDescription] = useState('')
  const [interpreting, setInterpreting] = useState(false)
  const [suggestion, setSuggestion] = useState<any>(null)
  const [interpretError, setInterpretError] = useState('')
  const [confirming, setConfirming] = useState(false)

  const recommended = profile?.path_options?.find((o: any) => o.key === 'recommended')
  const defaultCert = recommended?.certifications?.[0] ?? profile?.active_certification ?? ''
  const [selectedCert, setSelectedCert] = useState(defaultCert)

  async function handleInterpret(e: FormEvent) {
    e.preventDefault()
    if (!description.trim()) return
    setInterpreting(true)
    setInterpretError('')
    setSuggestion(null)
    try {
      const result = await api.interpretPath(description.trim())
      setSuggestion(result)
      setSelectedCert(result.certification)
    } catch (ex: any) {
      setInterpretError(ex.message ?? 'Unable to interpret your goal. Try again.')
    } finally {
      setInterpreting(false)
    }
  }

  async function handleConfirm() {
    const path = tab === 'recommended' ? 'recommended' : 'custom'
    const cert = tab === 'recommended' ? selectedCert : (suggestion?.certification ?? selectedCert)
    setConfirming(true)
    try {
      await onConfirm(path, cert)
    } finally {
      setConfirming(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0d1117]/90 p-4">
      <div className="w-full max-w-xl rounded-3xl border border-[#30363d] bg-[#161b22] shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="border-b border-[#30363d] px-6 pt-6 pb-4">
          <div className="text-xl font-semibold text-github-text">Choose your learning path</div>
          <p className="mt-1 text-sm text-github-muted">
            ASCENT will personalise your study plan, milestones, and practice questions around your chosen path.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[#30363d]">
          {([['recommended', '⭐ Recommended for me'], ['describe', '✏️ Describe my goal']] as [Tab, string][]).map(([key, label]) => (
            <button key={key} type="button" onClick={() => setTab(key)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition ${
                tab === key
                  ? 'border-b-2 border-github-blue text-github-text'
                  : 'text-github-muted hover:text-github-text'
              }`}>
              {label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="px-6 py-5 space-y-4">

          {tab === 'recommended' && (
            <>
              {recommended ? (
                <div className="rounded-2xl border border-github-border bg-github-bg p-4">
                  <div className="font-medium text-github-text">{recommended.title}</div>
                  <div className="mt-1 text-sm text-github-muted">{recommended.description}</div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {recommended.certifications?.map((c: string) => <Badge key={c} label={c} variant="blue" />)}
                  </div>
                </div>
              ) : (
                <div className="text-sm text-github-muted">Loading recommended path…</div>
              )}
              {recommended?.certifications?.length > 1 && (
                <div>
                  <label className="text-sm text-github-muted">Start with</label>
                  <select value={selectedCert} onChange={e => setSelectedCert(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-github-border bg-github-surface px-3 py-2 text-sm text-github-text focus:outline-none focus:ring-2 focus:ring-github-blue">
                    {recommended.certifications.map((c: string) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              )}
            </>
          )}

          {tab === 'describe' && (
            <>
              <form onSubmit={handleInterpret} className="space-y-3">
                <label className="block text-sm text-github-muted">
                  Describe your role, goals, or the skills you want to build:
                </label>
                <textarea
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  placeholder="e.g. I'm a backend developer who wants to move into cloud architecture, I already know Python and some Azure basics…"
                  rows={3}
                  className="w-full rounded-xl border border-github-border bg-github-bg px-4 py-3 text-sm text-github-text placeholder:text-github-muted focus:outline-none focus:ring-2 focus:ring-github-blue resize-none"
                />
                <button type="submit" disabled={interpreting || !description.trim()}
                  className="rounded-xl bg-github-blue px-4 py-2 text-sm font-semibold text-[#0d1117] hover:bg-github-blue/80 disabled:opacity-50 transition">
                  {interpreting ? 'Analysing…' : 'Suggest a path for me'}
                </button>
              </form>

              {interpretError && (
                <div className="rounded-xl border border-github-red/30 bg-github-red/10 px-4 py-3 text-sm text-github-red">
                  {interpretError}
                </div>
              )}

              {suggestion && (
                <div className="rounded-2xl border border-github-green/30 bg-github-green/5 p-4 space-y-2">
                  <div className="text-sm font-medium text-github-text">AI suggestion</div>
                  <div className="flex items-center gap-2">
                    <Badge label={suggestion.certification} variant="blue" />
                    <span className="text-sm text-github-text">{suggestion.cert_title}</span>
                  </div>
                  <p className="text-sm text-github-muted">{suggestion.reasoning}</p>
                  <div className="flex flex-wrap gap-1 pt-1">
                    {suggestion.skills?.map((s: string) => <Badge key={s} label={s} variant="slate" />)}
                  </div>
                  <div className="text-xs text-github-muted">~{suggestion.recommended_hours}h recommended study</div>
                  {suggestion.available_certifications?.length > 1 && (
                    <div>
                      <label className="text-xs text-github-muted">Or choose a different cert</label>
                      <select value={suggestion.certification}
                        onChange={e => setSuggestion({ ...suggestion, certification: e.target.value })}
                        className="mt-1 w-full rounded-xl border border-github-border bg-github-surface px-3 py-2 text-sm text-github-text focus:outline-none focus:ring-2 focus:ring-github-blue">
                        {suggestion.available_certifications.map((c: string) => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-[#30363d] px-6 py-4 gap-3">
          <button type="button" onClick={onDismiss}
            className="rounded-xl border border-github-border px-4 py-2 text-sm text-github-muted hover:text-github-text hover:bg-github-border/20 transition">
            Skip for now
          </button>
          <button type="button" onClick={handleConfirm}
            disabled={confirming || (tab === 'describe' && !suggestion)}
            className="rounded-xl bg-github-blue px-5 py-2 text-sm font-semibold text-[#0d1117] hover:bg-github-blue/80 disabled:opacity-50 transition">
            {confirming ? 'Saving…' : 'Start my learning journey →'}
          </button>
        </div>

      </div>
    </div>
  )
}
