import { useState, useRef, useEffect, type FormEvent } from 'react'
import { api } from '../api'
import { TraceTimeline } from './TraceTimeline'
import { Badge } from './Badge'
import { CitationChip } from './CitationChip'

interface Message {
  id: number
  role: 'user' | 'assistant'
  text: string
  result?: any
  loading?: boolean
}

const SUGGESTIONS = [
  'Am I ready to book the exam?',
  'Build me a 6-week plan',
  'Focus on Azure Functions',
  'What are my weakest skills?',
]

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 0, role: 'assistant', text: "Hi! I'm your ASCENT learning assistant. Ask me anything about your certification preparation — I'll analyse your profile and build a personalised plan." }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const nextId = useRef(1)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send(text: string) {
    if (!text.trim() || loading) return
    const userMsg: Message = { id: nextId.current++, role: 'user', text }
    const thinkingMsg: Message = { id: nextId.current++, role: 'assistant', text: '', loading: true }
    setMessages(prev => [...prev, userMsg, thinkingMsg])
    setInput('')
    setLoading(true)
    try {
      const data = await api.chat(text)
      setMessages(prev => prev.map(m =>
        m.id === thinkingMsg.id
          ? { ...m, text: data.reply, result: data.result, loading: false }
          : m
      ))
    } catch (e: any) {
      setMessages(prev => prev.map(m =>
        m.id === thinkingMsg.id
          ? { ...m, text: `Sorry, something went wrong: ${e.message}`, loading: false }
          : m
      ))
    } finally {
      setLoading(false)
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    send(input)
  }

  return (
    <div className="flex h-[650px] w-full max-w-[380px] flex-col overflow-hidden rounded-2xl border border-[#30363d] bg-[#161b22] shadow-sm">
      <div className="shrink-0 border-b border-[#30363d] bg-github-blue/10 px-5 py-4">
        <div className="flex items-center gap-3">
          <span className="text-xl">🤖</span>
          <div>
            <div className="text-sm font-semibold text-github-text">ASCENT AI Assistant</div>
            <div className="text-xs text-github-muted">Powered by Foundry IQ · Synthetic demo</div>
          </div>
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
        <div className="space-y-4">
          {messages.map(msg => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] ${msg.role === 'user'
                ? 'rounded-2xl rounded-tr-sm bg-github-blue px-4 py-3 text-github-bg'
                : 'rounded-2xl rounded-tl-sm border border-[#30363d] bg-[#0d1117]/60 px-4 py-4'}`}>

                {msg.loading ? (
                  <div className="flex items-center gap-2 py-2">
                    {[0, 1, 2].map(i => (
                      <div key={i} className="h-2.5 w-2.5 animate-bounce rounded-full bg-github-muted" style={{ animationDelay: `${i * 0.15}s` }} />
                    ))}
                  </div>
                ) : (
                  <>
                    <p className={`text-sm ${msg.role === 'user' ? 'text-github-bg' : 'text-github-text'}`}>{msg.text}</p>
                    {msg.result && (
                      <div className="mt-4 space-y-3">
                        <div className="flex flex-wrap gap-2">
                          <Badge label={msg.result.passed ? 'READY' : 'IN PREPARATION'} variant={msg.result.passed ? 'green' : 'amber'} />
                          {msg.result.next_step && <Badge label={`Next: ${msg.result.next_step}`} variant="blue" />}
                          {msg.result.loops > 0 && <Badge label={`${msg.result.loops} loop${msg.result.loops > 1 ? 's' : ''}`} variant="purple" />}
                        </div>
                        {msg.result.study_plan && (
                          <div className="grid grid-cols-3 gap-2 text-xs">
                            {[
                              { label: 'Cert', val: msg.result.study_plan.certification || 'TBD' },
                              { label: 'Weeks', val: `${msg.result.study_plan.weeks}w` },
                              { label: 'Hours/wk', val: `${msg.result.study_plan.hours_per_week}h` },
                            ].map(({ label, val }) => (
                              <div key={label} className="rounded-xl border border-[#30363d] bg-[#0d1117] px-2 py-2 text-center">
                                <div className="text-github-muted">{label}</div>
                                <div className="font-semibold text-github-text">{val}</div>
                              </div>
                            ))}
                          </div>
                        )}
                        {msg.result.curator?.citations?.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            {[...new Set(msg.result.curator.citations as string[])].map((c: string) => (
                              <CitationChip key={c} source={c} />
                            ))}
                          </div>
                        )}
                        {msg.result.trace?.length > 0 && (
                          <TraceTimeline trace={msg.result.trace} />
                        )}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="sticky bottom-0 shrink-0 border-t border-[#30363d] bg-[#161b22] px-5 py-4">
        <div className="mb-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map(s => (
            <button key={s} type="button" onClick={() => send(s)}
              className="rounded-full border border-github-blue/50 bg-[#0d1117] px-3 py-1.5 text-xs font-medium text-github-blue transition-colors hover:bg-github-blue/10">
              {s}
            </button>
          ))}
        </div>
        <form onSubmit={submit} className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask about your preparation…"
            className="flex-1 rounded-xl border border-[#30363d] bg-[#0d1117] px-4 py-3 text-sm text-github-text placeholder-github-muted focus:outline-none focus:ring-2 focus:ring-github-blue disabled:opacity-50"
          />
          <button type="submit" disabled={loading || !input.trim()}
            className="rounded-xl bg-github-blue px-5 py-3 text-sm font-semibold text-[#0d1117] transition hover:bg-github-blue/80 disabled:opacity-40">
            Send
          </button>
        </form>
        <div className="mt-2 text-center text-xs text-github-muted">
          AI system · Synthetic demo data only
        </div>
      </div>
    </div>
  )
}
