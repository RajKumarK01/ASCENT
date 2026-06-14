import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { usePlan } from '../context/PlanContext'
import { Card } from '../components/Card'
import { ContributionHeatmap, type ContributionData, type ScheduledMap } from '../components/ContributionHeatmap'
import { PathSetupModal } from '../components/PathSetupModal'
import { LoadingScreen } from '../components/LoadingScreen'

function formatDate(date: Date) {
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function calculateStreaks(data: ContributionData) {
  const today = new Date()
  let currentStreak = 0
  let longestStreak = 0
  let runningStreak = 0
  let activeDays = 0

  for (let daysAgo = 364; daysAgo >= 0; daysAgo--) {
    const date = new Date(today)
    date.setDate(date.getDate() - daysAgo)
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    const count = data[key] ?? 0
    if (count > 0) {
      runningStreak += 1
      activeDays += 1
    } else {
      longestStreak = Math.max(longestStreak, runningStreak)
      runningStreak = 0
    }
  }
  longestStreak = Math.max(longestStreak, runningStreak)

  for (let daysAgo = 0; daysAgo <= 364; daysAgo++) {
    const date = new Date(today)
    date.setDate(date.getDate() - daysAgo)
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    if ((data[key] ?? 0) > 0) {
      currentStreak += 1
    } else {
      break
    }
  }

  return { currentStreak, longestStreak, activeDays }
}

export function EmployeeDashboard() {
  const { data, contributions, loading, error: err, refresh: loadDashboard } = usePlan()
  const contribLoading = false
  const [showPathModal, setShowPathModal] = useState(false)

  async function handlePathConfirm(path: string, certification: string) {
    await api.updateProfile({ path, certification })
    await loadDashboard()
    setShowPathModal(false)
  }

  const profile = data?.profile ?? {}
  const r = data?.assessment?.readiness ?? {}

  // Readiness & assessment score are REAL — driven by the assessment the learner takes.
  const asmt = profile.assessment ?? { taken: false, score_pct: 0, attempts: 0, date: null }
  const assessmentTaken = !!asmt.taken
  const readinessPct = r.pass_threshold
    ? Math.max(0, Math.min(100, Math.round(((r.pass_threshold - (r.score_gap ?? 0)) / r.pass_threshold) * 100)))
    : 0

  const completedModules = profile.progress?.completed ?? 0
  const totalModules = profile.progress?.total ?? 0
  const studyProgress = totalModules ? Math.round((completedModules / totalModules) * 100) : 0
  const lastAssessmentDate = asmt.date ?? '—'
  const currentChain = profile.certification_chain ?? []
  const activeCertification = profile.active_certification ?? profile.path_title
  const { currentStreak, longestStreak, activeDays } = useMemo(() => calculateStreaks(contributions), [contributions])

  const totalActivities = useMemo(() => Object.values(contributions).reduce((sum, value) => sum + value, 0), [contributions])
  const contributionsLast30 = useMemo(() => {
    const today = new Date()
    return Object.entries(contributions).reduce((sum, [date, value]) => {
      const [year, month, day] = date.split('-').map(Number)
      const dt = new Date(year, month - 1, day)
      const diffDays = Math.floor((today.getTime() - dt.getTime()) / 86400000)
      return diffDays >= 0 && diffDays < 30 ? sum + value : sum
    }, 0)
  }, [contributions])
  const readinessImpact = assessmentTaken ? Math.max(0, Math.round(readinessPct / 8)) : 0

  // Upcoming study/assessment sessions to overlay on the heatmap's future side.
  const scheduled = useMemo<ScheduledMap>(() => {
    const m: ScheduledMap = {}
    const evs: any[] = data?.study_plan?.schedule ?? []
    for (const ev of evs) {
      if (!ev?.date) continue
      if (m[ev.date] !== 'study') m[ev.date] = ev.type === 'assessment' ? 'assessment' : 'study'
    }
    return m
  }, [data])
  const upcomingCount = Object.keys(scheduled).length

  if (loading && !data) {
    return <LoadingScreen />
  }

  if (err && !data) {
    return (
      <div className="p-8 max-w-3xl mx-auto space-y-4 rounded-3xl border border-github-border bg-github-surface">
        <div className="text-lg font-semibold text-github-text">Unable to load your dashboard</div>
        <div className="text-sm text-github-red">{err}</div>
        <button type="button" onClick={() => loadDashboard()} className="rounded-2xl bg-github-blue px-4 py-3 text-sm font-semibold text-github-bg hover:bg-github-blue/80">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="relative mx-auto max-w-7xl p-6">
      {showPathModal && profile && (
        <PathSetupModal
          profile={profile}
          onConfirm={handlePathConfirm}
          onDismiss={() => setShowPathModal(false)}
        />
      )}

      <div className="space-y-6">
        <main className="min-w-0 space-y-6">
          <div className="grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(200px,1fr)]">
            <div className="space-y-2">
              <div className="text-sm text-github-muted">Welcome back, {profile.learner_id}</div>
              <h1 className="text-3xl font-semibold tracking-tight text-github-text">Your learning dashboard</h1>
              <p className="max-w-2xl text-sm text-github-muted">Track your certification readiness, study progress, and learning activity in one dashboard.</p>
            </div>
            <div className="rounded-2xl border border-[#30363d] bg-[#161b22] p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm text-github-muted">Path type</div>
                  <div className="mt-1 text-lg font-semibold text-github-text">{profile.selected_path?.toUpperCase() ?? 'RECOMMENDED'}</div>
                </div>
                <button type="button" onClick={() => setShowPathModal(true)} className="rounded-xl bg-github-blue px-4 py-2 text-sm font-semibold text-[#0d1117] hover:bg-github-blue/80">Change path</button>
              </div>
              <div className="mt-4 space-y-2 text-sm text-github-muted">
                <div>Active certification: <span className="font-medium text-github-text">{activeCertification}</span></div>
                <div>Current streak: <span className="font-medium text-github-text">{currentStreak} day{currentStreak === 1 ? '' : 's'}</span></div>
                <div>Active days: <span className="font-medium text-github-text">{activeDays}</span></div>
              </div>
            </div>
          </div>

          {/* Take-assessment call to action — shown until the learner takes their assessment */}
          {!assessmentTaken && (
            <div className="flex flex-col gap-3 rounded-2xl border border-github-blue/40 bg-github-blue/10 p-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="text-base font-semibold text-github-text">📝 Take your assessment</div>
                <p className="mt-1 text-sm text-github-muted">
                  Your readiness and assessment score are calculated from a real practice assessment for <span className="font-medium text-github-text">{activeCertification}</span>. Take it now to unlock them.
                </p>
              </div>
              <Link to="/assessment" className="shrink-0 rounded-xl bg-github-blue px-5 py-2.5 text-sm font-semibold text-[#0d1117] hover:bg-github-blue/80">
                Start assessment →
              </Link>
            </div>
          )}

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="flex h-full flex-col">
              <div className="text-sm text-github-muted">Readiness score</div>
              <div className="mt-3 text-3xl font-semibold text-github-text">{assessmentTaken ? `${readinessPct}%` : '—'}</div>
              <div className="mt-auto pt-3 text-xs text-github-muted">
                {assessmentTaken ? 'Based on your latest assessment and study hours.' : 'Take your assessment to calculate readiness.'}
              </div>
            </Card>
            <Card className="flex h-full flex-col">
              <div className="text-sm text-github-muted">Assessment score</div>
              <div className="mt-3 text-3xl font-semibold text-github-text">{assessmentTaken ? `${asmt.score_pct}%` : '—'}</div>
              {assessmentTaken ? (
                <div className="mt-auto pt-3 text-xs text-github-muted">
                  <div>Last assessment: {lastAssessmentDate}</div>
                  <div>Attempts: {asmt.attempts}</div>
                </div>
              ) : (
                <Link to="/assessment" className="mt-auto pt-3 text-xs font-medium text-github-blue hover:underline">Take assessment →</Link>
              )}
            </Card>
            <Card className="flex h-full flex-col">
              <div className="text-sm text-github-muted">Study progress</div>
              <div className="mt-3 text-3xl font-semibold text-github-text">{studyProgress}%</div>
              <div className="mt-auto pt-3 text-xs text-github-muted">{completedModules}/{totalModules} modules completed</div>
            </Card>
            <Card className="flex h-full flex-col">
              <div className="text-sm text-github-muted">Current streak</div>
              <div className="mt-3 text-3xl font-semibold text-github-text">{currentStreak}</div>
              <div className="mt-auto pt-3 text-xs text-github-muted">days active</div>
            </Card>
            <Card className="flex h-full flex-col">
              <div className="text-sm text-github-muted">Completed modules</div>
              <div className="mt-3 text-3xl font-semibold text-github-text">{completedModules}</div>
              <div className="mt-auto pt-3 text-xs text-github-muted">on your current path</div>
            </Card>
            <Card className="flex h-full flex-col">
              <div className="text-sm text-github-muted">Active certifications</div>
              <div className="mt-3 text-3xl font-semibold text-github-text">{currentChain.length}</div>
              <div className="mt-auto pt-3 text-xs text-github-muted">certifications in your track</div>
            </Card>
          </div>

          <Card title="Learning Activity">
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_240px]">
              <div className="min-w-0">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-sm text-github-muted">GitHub-style heatmap</div>
                    <div className="mt-1 text-lg font-semibold text-github-text">Track your learning contributions</div>
                  </div>
                  <div className="text-sm text-github-muted">
                    {contributionsLast30} contributions in the last 30 days
                    {upcomingCount > 0 && <span className="ml-2 text-github-blue">· {upcomingCount} sessions scheduled ahead</span>}
                  </div>
                </div>
                <ContributionHeatmap data={contributions} loading={contribLoading} scheduled={scheduled} />
              </div>

              <div className="flex h-full flex-col justify-between rounded-2xl border border-[#30363d] bg-[#0d1117]/40 p-6">
                <div className="text-sm font-semibold text-github-muted">Statistics</div>
                <div className="mt-4 space-y-4 text-sm">
                  <div>
                    <div className="text-github-muted">Current Streak</div>
                    <div className="mt-1 text-lg font-semibold text-github-text">{currentStreak} days</div>
                  </div>
                  <div>
                    <div className="text-github-muted">Longest Streak</div>
                    <div className="mt-1 text-lg font-semibold text-github-text">{longestStreak} days</div>
                  </div>
                  <div>
                    <div className="text-github-muted">Active Days</div>
                    <div className="mt-1 text-lg font-semibold text-github-text">{activeDays}</div>
                  </div>
                  <div>
                    <div className="text-github-muted">Total Activities</div>
                    <div className="mt-1 text-lg font-semibold text-github-text">{totalActivities}</div>
                  </div>
                  <div>
                    <div className="text-github-muted">Readiness Impact</div>
                    <div className="mt-1 text-lg font-semibold text-github-green">+{readinessImpact}%</div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </main>
      </div>
    </div>
  )
}
