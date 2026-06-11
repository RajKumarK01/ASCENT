import { useState } from 'react'
import { api } from '../api'
import { usePlan } from '../context/PlanContext'
import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { CitationChip } from '../components/CitationChip'

const STATUS_VARIANTS: Record<string, 'green' | 'blue' | 'slate'> = {
  complete: 'green',
  'in progress': 'blue',
  'not started': 'slate',
}

const DIFFICULTY_LEVELS = ['Beginner', 'Intermediate', 'Advanced']

function buildResources(skill: string) {
  const query = encodeURIComponent(`${skill} Azure`)
  return [
    { label: 'Microsoft Learn', url: `https://learn.microsoft.com/search/?terms=${query}` },
    { label: 'Documentation', url: `https://learn.microsoft.com/search/?terms=${query}` },
    { label: 'Practice Lab', url: `https://learn.microsoft.com/search/?terms=${query}+lab` },
  ]
}

function buildVideo(skill: string, certification: string) {
  const query = encodeURIComponent(`${skill} ${certification} tutorial`)
  return {
    title: `${skill} fundamentals for ${certification}`,
    duration: '12:34',
    url: `https://www.youtube.com/results?search_query=${query}`,
  }
}

export function StudyPlan() {
  const { data, loading, error, weeks, setWeeks, refresh } = usePlan()
  const [completing, setCompleting] = useState<string | null>(null)

  async function handleCompleteModule(moduleId: string) {
    setCompleting(moduleId)
    try {
      await api.completeModule(moduleId)
      await refresh()
    } finally {
      setCompleting(null)
    }
  }

  const plan = data?.study_plan
  const profile = data?.profile
  const cur = data?.curator
  const progressPercent = profile?.progress?.total ? Math.round((profile.progress.completed / profile.progress.total) * 100) : 0

  return (
    <div className="p-6 space-y-5 max-w-6xl mx-auto">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-github-text">Study Plan</h1>
          <p className="text-sm text-github-muted mt-1">A module-level journey designed around your current certification and career goals.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {[4, 6, 8, 12].map(w => (
            <button key={w} onClick={() => setWeeks(w)}
              className={`rounded-2xl border px-4 py-2 text-sm font-medium transition ${weeks === w ? 'bg-github-blue text-github-bg border-github-blue' : 'border-github-border text-github-muted hover:bg-github-border/30'}`}>
              {w}w
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="text-github-muted">Loading…</div>}
      {error && <div className="text-sm text-github-red bg-github-red/10 border border-github-red/20 rounded-xl p-3">{error}</div>}

      {!loading && plan && (
        <div className="space-y-6">
          <Card>
            <div className="grid gap-4 sm:grid-cols-3 text-sm text-github-muted">
              <div>
                <div className="uppercase tracking-wide">Total hours</div>
                <div className="mt-2 text-2xl font-semibold text-github-text">{plan.total_recommended_hours}h</div>
              </div>
              <div>
                <div className="uppercase tracking-wide">Duration</div>
                <div className="mt-2 text-2xl font-semibold text-github-text">{plan.weeks} weeks</div>
              </div>
              <div>
                <div className="uppercase tracking-wide">Hours / week</div>
                <div className="mt-2 text-2xl font-semibold text-github-text">{plan.hours_per_week}h</div>
              </div>
            </div>
            {plan.prerequisites?.length > 0 && (
              <div className="mt-4 text-sm text-github-muted">
                <span className="font-medium text-github-text">Prerequisites:</span>
                <div className="mt-2 flex flex-wrap gap-2">
                  {plan.prerequisites.map((p: string) => <Badge key={p} label={p} variant="amber" />)}
                </div>
              </div>
            )}
          </Card>

          {profile && (
            <Card title="Module progress">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="text-sm text-github-muted">Path</div>
                  <div className="mt-2 text-xl font-semibold text-github-text">{profile.active_certification}</div>
                </div>
                <div className="rounded-2xl border border-github-border bg-github-bg px-4 py-3 text-sm">
                  <div className="text-github-muted">Completed</div>
                  <div className="mt-2 text-xl font-semibold text-github-text">{profile.progress?.completed ?? 0}/{profile.progress?.total ?? 0}</div>
                </div>
                <div className="rounded-2xl border border-github-border bg-github-bg px-4 py-3 text-sm">
                  <div className="text-github-muted">Progress</div>
                  <div className="mt-2 text-xl font-semibold text-github-text">{progressPercent}%</div>
                </div>
              </div>
            </Card>
          )}

          {profile?.modules?.length > 0 ? (
            <div className="grid gap-6">
              {profile.modules.map((module: any, index: number) => {
                const status = module.status || 'not started'
                const badgeVariant = STATUS_VARIANTS[status] ?? 'slate'
                const resources = buildResources(module.skill)
                const video = buildVideo(module.skill, profile.active_certification ?? '')
                const difficulty = DIFFICULTY_LEVELS[index % DIFFICULTY_LEVELS.length]

                return (
                  <Card key={module.id} className="p-6">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="space-y-3">
                        <div className="text-sm text-github-muted">Module</div>
                        <div className="text-xl font-semibold text-github-text">{module.title}</div>
                        <div className="text-sm text-github-muted">{module.skill}</div>
                        <div className="grid gap-3 sm:grid-cols-3 text-sm">
                          <div>
                            <div className="text-github-muted">Status</div>
                            <div className="mt-1"><Badge label={status.replace('-', ' ').toUpperCase()} variant={badgeVariant} /></div>
                          </div>
                          <div>
                            <div className="text-github-muted">Estimated time</div>
                            <div className="mt-1 text-github-text">{module.target_hours}h</div>
                          </div>
                          <div>
                            <div className="text-github-muted">Difficulty</div>
                            <div className="mt-1 text-github-text">{difficulty}</div>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col gap-3 sm:items-end">
                        <button type="button" disabled={status === 'complete' || completing === module.id}
                          onClick={() => handleCompleteModule(module.id)}
                          className={`rounded-2xl px-4 py-3 text-sm font-semibold transition ${status === 'complete' ? 'bg-github-border/20 text-github-muted cursor-not-allowed' : 'bg-github-blue text-github-bg hover:bg-github-blue/80'}`}>
                          {status === 'complete' ? 'Completed' : completing === module.id ? 'Updating…' : 'Mark complete'}
                        </button>
                        <div className="text-right text-xs text-github-muted">{status === 'complete' ? 'Well done — keep the momentum.' : 'Finish this module to update your progress.'}</div>
                      </div>
                    </div>

                    <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
                      <div className="space-y-4">
                        <div>
                          <div className="text-sm font-semibold text-github-text">Resources</div>
                          <div className="mt-3 grid gap-3 sm:grid-cols-3">
                            {resources.map(resource => (
                              <a key={resource.label} href={resource.url} target="_blank" rel="noreferrer" className="rounded-2xl border border-github-border bg-github-bg px-4 py-3 text-sm text-github-text transition hover:border-github-blue/50 hover:bg-github-border/30">
                                <div className="font-semibold">{resource.label}</div>
                                <div className="text-xs text-github-muted mt-1">Open in new tab</div>
                              </a>
                            ))}
                          </div>
                        </div>
                      </div>

                      <div className="rounded-3xl border border-github-border bg-github-surface p-4">
                        <div className="text-sm text-github-muted">Recommended Video</div>
                        <a href={video.url} target="_blank" rel="noreferrer" className="mt-4 block rounded-3xl border border-github-border bg-github-bg p-3 transition hover:border-github-blue/60 hover:bg-github-border/20">
                          <div className="aspect-video overflow-hidden rounded-2xl bg-github-border/70 flex items-center justify-center text-sm text-github-muted">YouTube thumbnail</div>
                          <div className="mt-3 text-sm font-semibold text-github-text">{video.title}</div>
                          <div className="mt-1 text-xs text-github-muted">{video.duration}</div>
                          <div className="mt-4 inline-flex items-center justify-center rounded-full bg-github-blue px-3 py-2 text-xs font-semibold text-github-bg">Watch Video</div>
                        </a>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          ) : (
            <Card>
              <div className="text-sm text-github-muted">No modules are available for your current path yet. Refresh the plan or choose a new journey.</div>
            </Card>
          )}

          <Card title="Milestones">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-github-muted text-xs uppercase border-b border-github-border">
                  <th className="pb-2 pr-4">Week</th>
                  <th className="pb-2 pr-4">Skill</th>
                  <th className="pb-2 pr-4">Hours</th>
                  <th className="pb-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {plan.milestones?.map((m: any, i: number) => (
                  <tr key={i} className="border-b border-github-border/30 hover:bg-github-border/20">
                    <td className="py-2 pr-4 font-medium text-github-text">{m.week}</td>
                    <td className="py-2 pr-4 text-github-text">{m.focus_skill}</td>
                    <td className="py-2 pr-4 text-github-muted">{m.target_hours}h</td>
                    <td className="py-2"><Badge label={m.is_gap ? 'Gap' : 'Reinforce'} variant={m.is_gap ? 'red' : 'slate'} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {cur?.microsoft_learn_modules?.length > 0 && (
            <Card title="Microsoft Learn — recommended modules">
              <p className="mb-3 text-xs text-github-muted">Curated via Microsoft Learn MCP · grounded in official exam objectives</p>
              <div className="space-y-2">
                {(cur.microsoft_learn_modules as string[]).map((url: string) => (
                  <a key={url} href={url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-2 rounded-xl border border-github-border bg-github-bg px-4 py-3 text-sm text-github-blue hover:border-github-blue/50 hover:bg-github-border/20 transition">
                    <span>📘</span>
                    <span className="truncate">{url.replace('https://learn.microsoft.com/en-us/training/paths/', '').replace(/\/$/, '').replace(/-/g, ' ')}</span>
                    <span className="ml-auto shrink-0 text-xs text-github-muted">learn.microsoft.com ↗</span>
                  </a>
                ))}
              </div>
            </Card>
          )}

          {cur?.citations?.length > 0 && (
            <Card title="Knowledge sources">
              <div className="flex flex-wrap gap-2">
                {[...new Set(cur.citations as string[])].map((c: string) => <CitationChip key={c} source={c} />)}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
