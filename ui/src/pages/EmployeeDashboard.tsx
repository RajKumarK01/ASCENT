import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { ProgressRing } from '../components/ProgressRing'
import { TraceTimeline } from '../components/TraceTimeline'
import { ChatPanel } from '../components/ChatPanel'
import { LoadingScreen } from '../components/LoadingScreen'

export function EmployeeDashboard() {
  const [data, setData] = useState<any>(null)
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.plan().then(setData).catch(e => setErr(e.message)).finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingScreen />
  if (err) return <div className="p-8 text-red-600">{err}</div>
  if (!data) return null

  const r = data.assessment?.readiness ?? {}
  const scorePct  = Math.min(100, (r.pass_threshold ? (data.assessment?.readiness?.score_gap === 0 ? 100 : ((r.pass_threshold - (r.score_gap ?? 0)) / r.pass_threshold) * 100) : 0))
  const hoursPct  = r.recommended_hours ? Math.min(100, ((r.recommended_hours - (r.hours_gap ?? 0)) / r.recommended_hours) * 100) : 0
  const readiness = data.assessment?.readiness
  const passed    = data.passed

  return (
    <div className="p-6 flex gap-6 max-w-6xl">
    {/* Left: dashboard cards */}
    <div className="flex-1 space-y-5 min-w-0">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">
            {data.curator?.role} &mdash; {data.curator?.certification}
          </h1>
          <p className="text-slate-500 text-sm mt-1">{data.learner_id}</p>
        </div>
        <Badge label={passed ? 'READY' : 'IN PREPARATION'} variant={passed ? 'green' : 'amber'} />
      </div>

      {/* Status banner */}
      <div className={`rounded-2xl p-4 border ${passed ? 'bg-emerald-50 border-emerald-200' : 'bg-amber-50 border-amber-200'}`}>
        {passed ? (
          <div className="text-sm text-emerald-800">
            <span className="font-semibold">Ready to book the exam.</span>
            {data.next_step && <span> Next certification: <span className="font-semibold">{data.next_step}</span></span>}
            {data.loops > 0 && <span className="text-emerald-600 ml-2">({data.loops} planning loop{data.loops > 1 ? 's' : ''} to reach readiness)</span>}
          </div>
        ) : (
          <div className="text-sm text-amber-800">
            <span className="font-semibold">Continue preparation.</span>
            {readiness?.score_gap > 0 && <span> Score gap: <strong>+{readiness.score_gap}%</strong> needed.</span>}
            {readiness?.hours_gap > 0 && <span> Hours gap: <strong>{readiness.hours_gap}h</strong> more study needed.</span>}
          </div>
        )}
        <p className="text-xs text-slate-500 mt-1">{data.human_in_the_loop}</p>
      </div>

      {/* Readiness rings */}
      <Card title="Readiness">
        <div className="flex gap-8 justify-center flex-wrap">
          <ProgressRing pct={scorePct} label="Practice score" sub={`${r.pass_threshold ?? 75}% threshold`} />
          <ProgressRing pct={hoursPct} label="Study hours" sub={`${r.recommended_hours ?? 20}h recommended`} />
        </div>
      </Card>

      {/* Engagement */}
      <Card title="Work rhythm & reminders">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-slate-500">Cadence</span><div className="font-medium mt-0.5">{data.engagement?.window?.cadence}</div></div>
          <div><span className="text-slate-500">Reminder time</span><div className="font-medium mt-0.5">{data.engagement?.window?.reminder_time}</div></div>
          <div className="col-span-2"><span className="text-slate-500">Policy</span><div className="mt-0.5 text-slate-700">{data.engagement?.reminder_policy}</div></div>
        </div>
        {data.engagement?.window?.capacity_constrained && (
          <div className="mt-3 text-xs bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-amber-700">
            High meeting load detected — condensed study sessions recommended
          </div>
        )}
      </Card>

      {/* Trace */}
      <Card title="Reasoning trace">
        <p className="text-xs text-slate-400 mb-2">Shows how the AI planned, curated, and verified your learning path.</p>
        <TraceTimeline trace={data.trace ?? []} />
      </Card>

      <div className="text-xs text-slate-400 text-center pb-4">{data.disclaimer}</div>
    </div>

    {/* Right: chat panel */}
    <div className="w-96 shrink-0 h-[calc(100vh-3rem)] sticky top-6">
      <ChatPanel />
    </div>
    </div>
  )
}
