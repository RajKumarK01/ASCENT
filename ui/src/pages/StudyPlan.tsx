import { useState, useCallback } from 'react'
import { api } from '../api'
import { usePlan } from '../context/PlanContext'
import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { CitationChip } from '../components/CitationChip'
import { TraceTimeline } from '../components/TraceTimeline'

const STATUS_VARIANTS: Record<string, 'green' | 'blue' | 'slate'> = {
  complete: 'green',
  'in progress': 'blue',
  'not started': 'slate',
}

const WEEK_OPTIONS = [4, 6, 8, 12]

type Video = { video_id: string; title: string; channel: string; thumbnail_url: string; url: string }

function YouTubeCard({ video, skill, certification }: { video?: Video | null; skill: string; certification: string }) {
  const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(`${certification} ${skill} tutorial Azure`)}`

  if (!video?.video_id) return (
    <a href={searchUrl} target="_blank" rel="noopener noreferrer"
       className="flex flex-col gap-2 rounded-3xl border border-github-border bg-github-surface p-4 hover:border-github-blue/50 transition">
      <div className="aspect-video rounded-2xl bg-github-border/30 flex items-center justify-center text-github-muted text-sm">
        <span>▶ Search on YouTube</span>
      </div>
      <div className="text-sm text-github-muted truncate">{skill} — {certification}</div>
    </a>
  )

  return (
    <a href={video.url} target="_blank" rel="noopener noreferrer"
       className="block rounded-3xl border border-github-border bg-github-surface overflow-hidden hover:border-github-blue/50 transition group">
      <div className="relative aspect-video overflow-hidden">
        <img
          src={video.thumbnail_url}
          alt={video.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          onError={e => { (e.target as HTMLImageElement).src = searchUrl; (e.target as HTMLImageElement).style.display='none' }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="rounded-full bg-black/70 px-4 py-3 text-white text-base font-bold">▶</div>
        </div>
      </div>
      <div className="p-3">
        <div className="text-sm font-semibold text-github-text line-clamp-2">{video.title}</div>
        <div className="mt-1 text-xs text-github-muted">{video.channel}</div>
      </div>
    </a>
  )
}

function ModuleCard({
  module, index, certification, onComplete, completing
}: {
  module: any; index: number; certification: string;
  onComplete: (id: string) => void; completing: string | null
}) {
  const [open, setOpen] = useState(false)
  const status = module.status || 'not started'
  const badgeVariant = STATUS_VARIANTS[status] ?? 'slate'
  const isML = module.source === 'microsoft_learn'

  return (
    <div className={`rounded-3xl border transition-all duration-200 ${open ? 'border-github-blue/60 bg-github-surface' : 'border-github-border bg-github-surface hover:border-github-border/80'}`}>
      {/* Header — always visible, click to expand */}
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        className="w-full text-left p-5"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3 min-w-0">
            <div className={`mt-0.5 shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
              ${status === 'complete' ? 'bg-github-green/20 text-github-green' : 'bg-github-border/50 text-github-muted'}`}>
              {status === 'complete' ? '✓' : index}
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-base font-semibold text-github-text">{module.title}</span>
                {isML && <span className="text-xs text-github-blue border border-github-blue/30 rounded-full px-2 py-0.5">MS Learn</span>}
              </div>
              <div className="mt-1 flex flex-wrap gap-2 items-center text-xs text-github-muted">
                <Badge label={status.replace('-', ' ').toUpperCase()} variant={badgeVariant} />
                <span>{module.target_hours}h</span>
                {module.skill && <span>· {module.skill}</span>}
              </div>
            </div>
          </div>
          <span className={`shrink-0 text-github-muted transition-transform ${open ? 'rotate-180' : ''}`}>▼</span>
        </div>
        {module.description && (
          <p className="mt-2 ml-11 text-xs text-github-muted line-clamp-2">{module.description}</p>
        )}
      </button>

      {/* Expanded content */}
      {open && (
        <div className="px-5 pb-5 ml-11 space-y-5 border-t border-github-border/30 pt-4">
          {/* Actions */}
          <div className="flex flex-wrap gap-3 items-center">
            <button
              type="button"
              disabled={status === 'complete' || completing === module.id}
              onClick={() => onComplete(module.id)}
              className={`rounded-2xl px-4 py-2 text-sm font-semibold transition
                ${status === 'complete' ? 'bg-github-border/20 text-github-muted cursor-not-allowed'
                : 'bg-github-blue text-github-bg hover:bg-github-blue/80'}`}
            >
              {status === 'complete' ? '✓ Completed' : completing === module.id ? 'Updating…' : 'Mark complete'}
            </button>
            {module.url && (
              <a href={module.url} target="_blank" rel="noopener noreferrer"
                 className="rounded-2xl border border-github-blue/40 px-4 py-2 text-sm text-github-blue hover:bg-github-blue/10 transition">
                Open on Microsoft Learn ↗
              </a>
            )}
          </div>

          {/* Resources — real Microsoft Learn deep links when available, else search fallback */}
          <div>
            <div className="text-xs font-semibold text-github-muted uppercase tracking-wide mb-2">
              Resources {module.resources?.length > 0 && <span className="text-github-green normal-case">· live Microsoft Learn links</span>}
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              {(module.resources?.length > 0
                ? (module.resources as { label: string; url: string }[])
                : [
                    { label: 'Microsoft Learn', url: `https://learn.microsoft.com/search/?terms=${encodeURIComponent(module.skill || module.title)}` },
                    { label: 'Official Docs', url: `https://learn.microsoft.com/search/?terms=${encodeURIComponent(module.title)}+documentation` },
                    { label: 'Practice Lab', url: `https://learn.microsoft.com/search/?terms=${encodeURIComponent(module.title)}+lab+hands-on` },
                  ]
              ).map(r => (
                <a key={r.url} href={r.url} target="_blank" rel="noopener noreferrer"
                   className="rounded-xl border border-github-border bg-github-bg px-3 py-2 text-xs text-github-text hover:border-github-blue/50 hover:bg-github-border/20 transition">
                  <div className="font-semibold line-clamp-2">{r.label}</div>
                  <div className="text-github-muted mt-0.5">Open ↗</div>
                </a>
              ))}
            </div>
          </div>

          {/* YouTube */}
          <div>
            <div className="text-xs font-semibold text-github-muted uppercase tracking-wide mb-2">Recommended video</div>
            <YouTubeCard video={module.youtube} skill={module.skill || module.title} certification={certification} />
          </div>
        </div>
      )}
    </div>
  )
}

export function StudyPlan() {
  const { data, loading, error, weeks, setWeeks, refresh } = usePlan()
  const [completing, setCompleting] = useState<string | null>(null)
  const [activeWeeks, setActiveWeeks] = useState(weeks)
  const [scheduling, setScheduling] = useState(false)
  const [calMsg, setCalMsg] = useState<string | null>(null)

  const handleWeeks = useCallback((w: number) => {
    setActiveWeeks(w)
    setWeeks(w)
  }, [setWeeks])

  async function handleCompleteModule(moduleId: string) {
    setCompleting(moduleId)
    try {
      await api.completeModule(moduleId)
      await refresh()
    } finally {
      setCompleting(null)
    }
  }

  async function handleSchedule() {
    setScheduling(true)
    setCalMsg(null)
    try {
      const res = await api.scheduleCalendar(activeWeeks)
      if (res.mode === 'graph') {
        setCalMsg(res.failed
          ? `Created ${res.created} event(s); ${res.failed} failed on ${res.target_user}.`
          : `✅ Added ${res.created} study + assessment events to ${res.target_user} (marked Busy).`)
      } else if (res.mode === 'ics' && res.ics) {
        const blob = new Blob([res.ics], { type: 'text/calendar' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = res.filename || 'ascent-study-plan.ics'
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
        setCalMsg(`📥 Downloaded a ${res.events.length}-event calendar (.ics) — open it to import into Outlook.`)
      }
    } catch (e: any) {
      setCalMsg(`❌ ${e?.message ?? 'Could not schedule the calendar.'}`)
    } finally {
      setScheduling(false)
    }
  }

  const plan = data?.study_plan
  const profile = data?.profile
  const cur = data?.curator
  const trace: string[] = data?.trace ?? []
  const certification = profile?.active_certification ?? cur?.certification ?? ''
  const progressPercent = profile?.progress?.total
    ? Math.round((profile.progress.completed / profile.progress.total) * 100) : 0

  return (
    <div className="p-6 space-y-5 max-w-6xl mx-auto">
      {/* Header + weeks selector */}
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-github-text">Study Plan</h1>
          <p className="text-sm text-github-muted mt-1">
            Module-level journey with Microsoft Learn content and YouTube video guides.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {WEEK_OPTIONS.map(w => (
            <button key={w} onClick={() => handleWeeks(w)}
              className={`rounded-2xl border px-4 py-2 text-sm font-medium transition
                ${activeWeeks === w
                  ? 'bg-github-blue text-github-bg border-github-blue shadow-md'
                  : 'border-github-border text-github-muted hover:bg-github-border/30'}`}>
              {w}w
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-github-muted text-sm p-4">
          <div className="w-4 h-4 rounded-full border-2 border-github-blue border-t-transparent animate-spin" />
          Calculating your {activeWeeks}-week plan…
        </div>
      )}
      {error && (
        <div className="text-sm text-github-red bg-github-red/10 border border-github-red/20 rounded-xl p-3">{error}</div>
      )}

      {!loading && plan && (
        <div className="space-y-6">
          {/* Plan summary */}
          <Card>
            <div className="grid gap-4 sm:grid-cols-4 text-sm text-github-muted">
              <div>
                <div className="uppercase tracking-wide text-xs">Total hours</div>
                <div className="mt-2 text-2xl font-semibold text-github-text">{plan.total_recommended_hours}h</div>
              </div>
              <div>
                <div className="uppercase tracking-wide text-xs">Duration</div>
                <div className="mt-2 text-2xl font-semibold text-github-text">{plan.weeks} weeks</div>
              </div>
              <div>
                <div className="uppercase tracking-wide text-xs">Hours / week</div>
                <div className="mt-2 text-2xl font-semibold text-github-text">{plan.hours_per_week}h</div>
              </div>
              <div>
                <div className="uppercase tracking-wide text-xs">Cadence</div>
                <div className="mt-2 text-sm font-semibold text-github-text">{plan.cadence ?? '—'}</div>
              </div>
            </div>
            {plan.preferred_day && (
              <div className="mt-3 rounded-xl border border-green-600/30 bg-green-600/10 px-3 py-2 text-xs text-green-400">
                📊 Work IQ signal: Most active on {plan.preferred_day}s — anchor your study block on this day.
              </div>
            )}
            {plan.prerequisites?.length > 0 && (
              <div className="mt-4 text-sm text-github-muted">
                <span className="font-medium text-github-text">Prerequisites: </span>
                <span className="flex flex-wrap gap-2 mt-1">
                  {plan.prerequisites.map((p: string) => <Badge key={p} label={p} variant="amber" />)}
                </span>
              </div>
            )}
          </Card>

          {/* Module progress bar */}
          {profile && (
            <Card title="Module progress">
              <div className="flex flex-wrap gap-4 sm:gap-8 items-center">
                <div>
                  <div className="text-xs text-github-muted">Certification</div>
                  <div className="mt-1 text-lg font-semibold text-github-text">{profile.active_certification}</div>
                </div>
                <div>
                  <div className="text-xs text-github-muted">Completed</div>
                  <div className="mt-1 text-lg font-semibold text-github-text">
                    {profile.progress?.completed ?? 0}/{profile.progress?.total ?? 0}
                  </div>
                </div>
                <div className="flex-1 min-w-[120px]">
                  <div className="text-xs text-github-muted mb-1">{progressPercent}% complete</div>
                  <div className="h-2 w-full rounded-full bg-github-border">
                    <div className="h-2 rounded-full bg-github-blue transition-all duration-500"
                         style={{ width: `${progressPercent}%` }} />
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Milestones table */}
          {plan.milestones?.length > 0 && (
            <Card title="Weekly milestones">
              {/* Schedule to Outlook (cross-tenant) — blocks the calendar with Busy events */}
              <div className="mb-3 flex flex-col gap-2 rounded-xl border border-github-blue/30 bg-github-blue/5 px-3 py-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-xs text-github-muted">
                  Schedule these study blocks &amp; assessments on your Outlook calendar (marked <span className="text-github-text font-medium">Busy</span>),
                  anchored to your most active day{plan.preferred_day ? <> (<span className="text-github-text">{plan.preferred_day}</span>)</> : null}.
                </div>
                <button type="button" onClick={handleSchedule} disabled={scheduling}
                  className="shrink-0 rounded-2xl bg-github-blue px-4 py-2 text-sm font-semibold text-github-bg hover:bg-github-blue/80 disabled:opacity-50">
                  {scheduling ? 'Scheduling…' : '📅 Add study plan to Outlook'}
                </button>
              </div>
              {calMsg && (
                <div className="mb-3 rounded-xl border border-github-border bg-github-bg px-3 py-2 text-xs text-github-text">{calMsg}</div>
              )}
              {plan.focus_skills?.length > 0 && (
                <div className="mb-3 flex flex-wrap items-center gap-2 rounded-xl border border-purple-500/30 bg-purple-500/10 px-3 py-2 text-xs text-purple-300">
                  <span className="font-semibold">🧠 Self-reflection priority:</span>
                  {(plan.focus_skills as string[]).map((s: string) => (
                    <span key={s} className="rounded-full bg-purple-500/20 px-2 py-0.5 font-mono">{s}</span>
                  ))}
                </div>
              )}
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-github-muted text-xs uppercase border-b border-github-border">
                    <th className="pb-2 pr-4">Week</th>
                    <th className="pb-2 pr-4">Skill</th>
                    <th className="pb-2 pr-4">Objective &amp; checkpoint</th>
                    <th className="pb-2 pr-4">Scheduled</th>
                    <th className="pb-2 pr-4">Hours</th>
                    <th className="pb-2">Priority</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.milestones.map((m: any, i: number) => (
                    <tr key={i} className={`border-b border-github-border/30 hover:bg-github-border/20 ${m.is_focus ? 'bg-purple-500/5' : ''}`}>
                      <td className="py-2 pr-4 font-medium text-github-text align-top">{m.week}</td>
                      <td className="py-2 pr-4 text-github-text align-top">
                        {m.focus_skill}
                        {m.is_focus && <span className="ml-2 text-xs text-purple-400">★ focus</span>}
                      </td>
                      <td className="py-2 pr-4 text-github-muted align-top max-w-md">
                        {m.objective && <div className="text-github-text">{m.objective}</div>}
                        {m.checkpoint && <div className="text-xs mt-0.5">✓ {m.checkpoint}</div>}
                      </td>
                      <td className="py-2 pr-4 text-github-muted align-top whitespace-nowrap text-xs">
                        {m.study_date && <div>📘 {m.study_date}</div>}
                        {m.assessment_date && <div className="mt-0.5">📝 {m.assessment_date}</div>}
                      </td>
                      <td className="py-2 pr-4 text-github-muted align-top">{m.target_hours}h</td>
                      <td className="py-2 align-top">
                        <Badge label={m.is_gap ? 'Gap' : 'Reinforce'} variant={m.is_gap ? 'red' : 'slate'} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}

          {/* Modules — expandable with YouTube */}
          {profile?.modules?.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold text-github-text">
                  Modules <span className="text-github-muted text-sm font-normal">({profile.modules.length})</span>
                </h2>
                <span className="text-xs text-github-muted">Click any module to expand resources & videos</span>
              </div>
              <div className="space-y-3">
                {profile.modules.map((module: any, index: number) => (
                  <ModuleCard
                    key={module.id}
                    module={module}
                    index={index + 1}
                    certification={certification}
                    onComplete={handleCompleteModule}
                    completing={completing}
                  />
                ))}
              </div>
            </div>
          )}

          {/* MS Learn modules */}
          {cur?.microsoft_learn_modules?.length > 0 && (
            <Card title="Microsoft Learn — recommended paths">
              <p className="mb-3 text-xs text-github-muted">
                {cur.grounding_sources?.includes('Microsoft Learn (live)')
                  ? '✅ Live results from Microsoft Learn search API · grounded in official exam objectives'
                  : '📋 Curated references · grounded in official exam objectives'}
              </p>
              <div className="space-y-2">
                {(cur.microsoft_learn_modules as string[]).map((url: string) => (
                  <a key={url} href={url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-2 rounded-xl border border-github-border bg-github-bg px-4 py-3 text-sm text-github-blue hover:border-github-blue/50 hover:bg-github-border/20 transition">
                    <span>📘</span>
                    <span className="truncate">{url.replace('https://learn.microsoft.com/en-us/training/', '').replace('paths/', '').replace(/\/$/, '').replace(/-/g, ' ')}</span>
                    <span className="ml-auto shrink-0 text-xs text-github-muted">learn.microsoft.com ↗</span>
                  </a>
                ))}
              </div>
            </Card>
          )}

          {/* Citations */}
          {cur?.citations?.length > 0 && (
            <Card title="Knowledge sources">
              <div className="flex flex-wrap gap-2">
                {[...new Set(cur.citations as string[])].map((c: string) => <CitationChip key={c} source={c} />)}
              </div>
            </Card>
          )}

          {/* Trace */}
          {trace.length > 0 && (
            <Card title="Agent reasoning trace">
              <TraceTimeline trace={trace} />
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
