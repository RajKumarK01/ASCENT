import { useState, useRef, useEffect, FormEvent } from 'react'
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
    <div className="flex flex-col h-full bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100 bg-indigo-50">
        <span className="text-lg">🤖</span>
        <div>
          <div className="text-sm font-semibold text-slate-800">ASCENT AI Assistant</div>
          <div className="text-xs text-slate-500">Powered by Foundry IQ · Synthetic demo</div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] ${msg.role === 'user'
              ? 'bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5'
              : 'bg-slate-50 border border-slate-100 rounded-2xl rounded-tl-sm px-4 py-3'}`}>

              {msg.loading ? (
                <div className="space-y-2 py-1">
                  <div className="flex gap-1 items-center">
                    {[0,1,2].map(i => (
                      <div key={i} className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: `${i*0.15}s` }} />
                    ))}
                    <span className="text-xs text-slate-400 ml-2">AI agents working…</span>
                  </div>
                  <div className="text-xs text-slate-400 italic">Querying Foundry IQ · GPT-4.1</div>
                </div>
              ) : (
                <>
                  <p className={`text-sm ${msg.role === 'user' ? 'text-white' : 'text-slate-800'}`}>{msg.text}</p>

                  {/* Rich result when assistant has a plan */}
                  {msg.result && (
                    <div className="mt-3 space-y-3">
                      {/* Status badge */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge label={msg.result.passed ? 'READY' : 'IN PREPARATION'} variant={msg.result.passed ? 'green' : 'amber'} />
                        {msg.result.next_step && <Badge label={`Next: ${msg.result.next_step}`} variant="blue" />}
                        {msg.result.loops > 0 && <Badge label={`${msg.result.loops} loop${msg.result.loops > 1 ? 's' : ''}`} variant="purple" />}
                      </div>

                      {/* Plan summary */}
                      {msg.result.study_plan && (
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          {[
                            { label: 'Cert', val: msg.result.study_plan.certification },
                            { label: 'Weeks', val: `${msg.result.study_plan.weeks}w` },
                            { label: 'Hours/wk', val: `${msg.result.study_plan.hours_per_week}h` },
                          ].map(({ label, val }) => (
                            <div key={label} className="bg-white rounded-lg px-2 py-1.5 border border-slate-200 text-center">
                              <div className="text-slate-400">{label}</div>
                              <div className="font-semibold text-slate-700">{val}</div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Citations */}
                      {msg.result.curator?.citations?.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {[...new Set(msg.result.curator.citations as string[])].map((c: string) => (
                            <CitationChip key={c} source={c} />
                          ))}
                        </div>
                      )}

                      {/* Trace (collapsible) */}
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

      {/* Suggestions */}
      {messages.length <= 2 && (
        <div className="px-4 pb-2 flex gap-2 flex-wrap">
          {SUGGESTIONS.map(s => (
            <button key={s} onClick={() => send(s)}
              className="text-xs px-3 py-1.5 rounded-full border border-indigo-200 text-indigo-600 hover:bg-indigo-50 transition-colors">
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <form onSubmit={submit} className="p-3 border-t border-slate-100 flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={loading}
          placeholder="Ask about your certification preparation…"
          className="flex-1 text-sm border border-slate-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50"
        />
        <button type="submit" disabled={loading || !input.trim()}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white px-4 py-2 rounded-xl text-sm font-medium transition-colors">
          Send
        </button>
      </form>

      <div className="px-4 pb-3 text-center text-xs text-slate-400">
        AI system · Synthetic demo data only
      </div>
    </div>
  )
}
