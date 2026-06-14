import { useEffect, useState } from 'react'
import { api } from '../api'

type Agent = { name: string; label: string; kind: string; description: string; sample: string }

export function AgentConsole() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selected, setSelected] = useState<Agent | null>(null)
  const [input, setInput] = useState('')
  const [reply, setReply] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  useEffect(() => {
    api.agents()
      .then(r => { setAgents(r.agents); if (r.agents[0]) { setSelected(r.agents[0]); setInput(r.agents[0].sample) } })
      .catch(e => setErr(e.message))
  }, [])

  function pick(a: Agent) {
    setSelected(a); setInput(a.sample); setReply(''); setErr('')
  }

  async function invoke() {
    if (!selected) return
    setLoading(true); setReply(''); setErr('')
    try {
      const r = await api.invokeAgent(selected.name, input)
      setReply(r.reply)
    } catch (e: any) {
      setErr(e.message ?? 'Invocation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-5">
        <h1 className="text-2xl font-bold text-github-text">Agent Console</h1>
        <p className="text-sm text-github-muted mt-1">
          Invoke each ASCENT agent live in Microsoft Foundry. The orchestrator is a hosted agent;
          the five specialists are independent Foundry prompt agents.
        </p>
      </div>

      {err && <div className="mb-4 rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300">{err}</div>}

      <div className="grid grid-cols-1 md:grid-cols-[280px_1fr] gap-5">
        {/* Agent list */}
        <div className="space-y-2">
          {agents.map(a => (
            <button key={a.name} onClick={() => pick(a)}
              className={`w-full text-left rounded-xl border px-3 py-3 transition-colors ${
                selected?.name === a.name
                  ? 'border-github-blue bg-github-blue/10'
                  : 'border-github-border bg-github-surface hover:border-github-blue/50'}`}>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-github-text text-sm">{a.label}</span>
                <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${
                  a.kind === 'hosted' ? 'bg-github-green/20 text-github-green' : 'bg-github-blue/20 text-github-blue'}`}>
                  {a.kind}
                </span>
              </div>
              <div className="text-xs text-github-muted mt-1 leading-snug">{a.description}</div>
            </button>
          ))}
        </div>

        {/* Invoke panel */}
        <div className="rounded-xl border border-github-border bg-github-surface p-4">
          {selected && (
            <>
              <div className="flex items-center gap-2 mb-3">
                <span className="font-semibold text-github-text">{selected.label}</span>
                <span className="text-xs text-github-muted font-mono">{selected.name}</span>
              </div>
              <textarea
                value={input} onChange={e => setInput(e.target.value)} rows={3}
                className="w-full rounded-xl border border-github-border bg-github-bg px-3 py-2 text-sm text-github-text focus:outline-none focus:border-github-blue"
                placeholder="Ask this agent…" />
              <div className="mt-3 flex items-center gap-3">
                <button onClick={invoke} disabled={loading}
                  className="rounded-xl bg-github-blue px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
                  {loading ? 'Reasoning…' : 'Invoke agent'}
                </button>
                {selected.kind === 'hosted' && (
                  <span className="text-xs text-github-muted">First call may cold-start the sandbox (~1 min).</span>
                )}
              </div>

              {reply && (
                <div className="mt-4">
                  <div className="text-xs text-github-muted mb-1">Agent response</div>
                  <pre className="whitespace-pre-wrap break-words rounded-xl border border-github-border bg-github-bg p-3 text-sm text-github-text font-sans">{reply}</pre>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
