import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { ChatPanel } from '../components/ChatPanel'
import { ContributionHeatmap, type ContributionData } from '../components/ContributionHeatmap'
import { CertificationPathModal } from '../components/CertificationPathModal'

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
  const [data, setData] = useState<any>(null)
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(true)
  const [contributions, setContributions] = useState<ContributionData>({})
  const [contribLoading, setContribLoading] = useState(false)
  const [showPathModal, setShowPathModal] = useState(false)
  const [selectedPath, setSelectedPath] = useState('recommended')
  const [selectedCertification, setSelectedCertification] = useState('')
  const [pathLoading, setPathLoading] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(false)

  async function loadDashboard() {
    setLoading(true)
    setErr('')

    try {
      setContribLoading(true)
      const [planData, contributionData] = await Promise.race([
        Promise.all([api.plan(), api.contributions()]),
        new Promise<never>((_, reject) => setTimeout(() => reject(new Error('timeout')), 10000)),
      ]) as [any, ContributionData]

      setData(planData)
      setContributions(contributionData)
      setShowPathModal(Boolean((planData as any)?.profile?.needs_selection))
    } catch (ex: any) {
      setErr(ex.message === 'timeout' ? 'Unable to load recommendations. Retry.' : ex.message ?? 'Unable to load dashboard')
    } finally {
      setLoading(false)
      setContribLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard()
  }, [])

  useEffect(() => {
    if (data?.profile) {
      setSelectedPath(data.profile.selected_path ?? 'recommended')
      setSelectedCertification(data.profile.active_certification ?? '')
    }
  }, [data])

  async function handlePathConfirm(path: string, certification: string) {
    setPathLoading(true)
    setErr('')
    try {
      await api.updateProfile({ path, certification })
      await loadDashboard()
      setShowPathModal(false)
    } catch (ex: any) {
      setErr(ex.message ?? 'Unable to save journey selection')
    } finally {
      setPathLoading(false)
    }
  }

  async function handlePathUpdate(path: string) {
    if (pathLoading) return
    const cert = selectedCertification || data?.profile?.active_certification || ''
    await handlePathConfirm(path, cert)
  }

  function handleDeletePath() {
    setDeleteConfirm(true)
  }

  function confirmDeletePath() {
    setDeleteConfirm(false)
    setShowPathModal(true)
    setData((prev: any) => prev ? {
      ...prev,
      profile: {
        ...prev.profile,
        needs_selection: true,
        modules: [],
        certification_chain: [],
        active_certification: '',
        path_title: 'Choose a learning journey to continue',
      },
    } : prev)
  }

  const profile = data?.profile ?? {}
  const r = data?.assessment?.readiness ?? {}
  const scorePct = Math.min(100, r.pass_threshold ? (r.pass_threshold - (r.score_gap ?? 0)) / r.pass_threshold * 100 : 0)
  const assessmentScore = r.pass_threshold ? Math.max(0, Math.min(100, Math.round(((r.pass_threshold - (r.score_gap ?? 0)) / r.pass_threshold) * 100))) : 0
  const completedModules = profile.progress?.completed ?? 0
  const totalModules = profile.progress?.total ?? 0
  const studyProgress = totalModules ? Math.round((completedModules / totalModules) * 100) : 0
  const attemptCount = 1 + (data?.loops ?? 0)
  const lastAssessmentDate = data?.assessment?.last_assessment_date ?? formatDate(new Date())
  const currentChain = profile.certification_chain ?? []
  const activeCertification = profile.active_certification ?? profile.path_title
  const pathOptions = profile.path_options ?? []
  const recommendedOption = pathOptions.find((option: any) => option.key === 'recommended')
  const customOption = pathOptions.find((option: any) => option.key === 'custom')
  const activeOption = pathOptions.find((option: any) => option.key === selectedPath) ?? recommendedOption ?? customOption
  const selectOptions = activeOption?.certifications ?? []
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
  const readinessImpact = Math.max(0, Math.round(scorePct / 8))

  if (loading && !data) {
    return (
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {[...Array(4)].map((_, idx) => (
          <div key={idx} className="h-40 animate-pulse rounded-3xl bg-github-border/30" />
        ))}
      </div>
    )
  }

  if (err && !data) {
    return (
      <div className="p-8 max-w-3xl mx-auto space-y-4 rounded-3xl border border-github-border bg-github-surface">
        <div className="text-lg font-semibold text-github-text">Unable to load your dashboard</div>
        <div className="text-sm text-github-red">{err}</div>
        <button type="button" onClick={loadDashboard} className="rounded-2xl bg-github-blue px-4 py-3 text-sm font-semibold text-github-bg hover:bg-github-blue/80">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="relative mx-auto max-w-7xl p-6">
      {showPathModal && (
        <CertificationPathModal profile={profile} onSubmit={handlePathConfirm} />
      )}

      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0d1117]/90 p-6">
          <div className="w-full max-w-lg rounded-3xl border border-[#30363d] bg-[#161b22] p-6 shadow-2xl">
            <div className="text-xl font-semibold text-github-text">Delete learning path</div>
            <p className="mt-3 text-sm text-github-muted">Are you sure you want to remove your current roadmap? This will let you choose a fresh path again.</p>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-end">
              <button type="button" onClick={() => setDeleteConfirm(false)} className="rounded-2xl border border-github-border px-4 py-3 text-sm text-github-text hover:bg-github-border/20">Cancel</button>
              <button type="button" onClick={confirmDeletePath} className="rounded-2xl bg-github-red px-4 py-3 text-sm font-semibold text-white hover:bg-github-red/90">Delete Path</button>
            </div>
          </div>
        </div>
      )}

          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
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

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="flex h-full flex-col">
              <div className="text-sm text-github-muted">Readiness score</div>
              <div className="mt-3 text-3xl font-semibold text-github-text">{Math.round(scorePct)}%</div>
              <div className="mt-auto pt-3 text-xs text-github-muted">Based on practice and study recommendations.</div>
            </Card>
            <Card className="flex h-full flex-col">
              <div className="text-sm text-github-muted">Assessment score</div>
              <div className="mt-3 text-3xl font-semibold text-github-text">{assessmentScore}%</div>
              <div className="mt-auto pt-3 text-xs text-github-muted">Last assessment: {lastAssessmentDate}</div>
              <div className="text-xs text-github-muted">Attempts: {attemptCount}</div>
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
                  <div className="text-sm text-github-muted">{contributionsLast30} contributions in the last 30 days</div>
                </div>
                <ContributionHeatmap data={contributions} loading={contribLoading} />
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

          <Card title="Learning path type">
            <div className="flex flex-wrap gap-2">
              {['recommended', 'custom'].map(option => {
                const active = selectedPath === option
                return (
                  <button key={option} type="button" onClick={() => {
                    setSelectedPath(option)
                    const optionData = pathOptions.find((item: any) => item.key === option)
                    setSelectedCertification(optionData?.certifications?.[0] ?? '')
                  }}
                    className={`rounded-full px-4 py-1.5 text-sm font-semibold transition ${active ? 'border border-github-blue bg-github-blue text-[#0d1117]' : 'border border-[#30363d] text-github-text hover:border-github-blue/60 hover:bg-[#30363d]/40'}`}>
                    {option === 'recommended' ? 'Recommended' : 'Custom'}
                  </button>
                )
              })}
            </div>
            {activeOption && (
              <div className="mt-4 rounded-xl border border-[#30363d] bg-[#0d1117] p-4">
                <div className="text-sm text-github-muted">{activeOption.title}</div>
                <div className="mt-1 text-base font-semibold text-github-text">{activeOption.description}</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {activeOption.certifications.map((cert: string) => (
                    <Badge key={cert} label={cert} variant="blue" />
                  ))}
                </div>
                {selectedPath === 'custom' && selectOptions.length > 1 && (
                  <div className="mt-3">
                    <label className="text-sm text-github-muted">Choose certification</label>
                    <select value={selectedCertification} onChange={e => setSelectedCertification(e.target.value)} className="mt-1 w-full rounded-xl border border-[#30363d] bg-[#161b22] px-4 py-2 text-sm text-github-text focus:outline-none focus:ring-2 focus:ring-github-blue">
                      {selectOptions.map((cert: string) => <option key={cert} value={cert}>{cert}</option>)}
                    </select>
                  </div>
                )}
              </div>
            )}
            <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <button type="button" onClick={() => handlePathUpdate(selectedPath)} disabled={pathLoading} className="rounded-xl bg-github-blue px-4 py-2 text-sm font-semibold text-[#0d1117] hover:bg-github-blue/80 disabled:opacity-50">
                Apply path selection
              </button>
              <button type="button" onClick={handleDeletePath} className="rounded-xl border border-[#30363d] px-4 py-2 text-sm text-github-text hover:bg-[#30363d]/30">
                Delete Path
              </button>
            </div>
          </Card>

          <Card title="Path summary">
            <div className="grid gap-3 md:grid-cols-2">
              {currentChain.map((cert: string, idx: number) => {
                const status = cert === activeCertification ? 'Current' : idx < currentChain.indexOf(activeCertification) ? 'Complete' : 'Upcoming'
                return (
                  <div key={cert} className="rounded-xl border border-[#30363d] bg-[#0d1117] p-4">
                    <div className="text-sm text-github-muted">{status}</div>
                    <div className="mt-1 text-base font-semibold text-github-text">{cert}</div>
                    <div className="mt-1 text-xs text-github-muted">Readiness: {status === 'Current' ? Math.round(scorePct) : 0}%</div>
                  </div>
                )
              })}
            </div>
          </Card>
        </main>

        <aside className="mx-auto min-w-0 w-full max-w-[380px] lg:mx-0">
          <ChatPanel />
        </aside>
      </div>
    </div>
  )
}
