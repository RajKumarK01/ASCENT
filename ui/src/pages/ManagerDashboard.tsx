import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card } from '../components/Card'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export function ManagerDashboard() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')

  useEffect(() => { api.insights().then(setData).catch(e => setErr(e.message)).finally(() => setLoading(false)) }, [])

  if (loading) return <div className="p-8 text-github-muted">Loading team insights…</div>
  if (err) return <div className="p-8 text-github-red">{err}</div>
  if (!data) return null

  const teams = Object.entries(data.teams ?? {}) as [string, any][]
  const chartData = teams.map(([name, v]) => ({
    name, Ready: v.ready, 'At Risk': v.at_risk, Constrained: v.capacity_constrained,
  }))

  return (
    <div className="p-6 space-y-5 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-github-text">Team Overview</h1>
        <p className="text-github-muted text-sm mt-1">Scope: {data.scope}</p>
      </div>

      {/* Privacy note */}
      <div className="bg-github-blue/10 border border-github-blue/50 rounded-xl p-3 text-xs text-github-blue flex items-start gap-2">
        <span>🔒</span>
        <span>This view shows aggregate team data only. No individual learner schedules, IDs, or personal details are exposed.</span>
      </div>

      {/* KPI tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {teams.map(([name, v]) => (
          <Card key={name} className="text-center">
            <div className="text-xs text-github-muted mb-1">{name}</div>
            <div className="text-2xl font-bold text-github-text">{v.readiness_rate}%</div>
            <div className="text-xs text-github-muted">ready</div>
            <div className="mt-2 flex justify-center gap-1 flex-wrap">
              {v.capacity_constrained > 0 && (
                <span className="text-xs bg-github-yellow/20 text-github-yellow px-1.5 py-0.5 rounded-full">{v.capacity_constrained} constrained</span>
              )}
              {v.at_risk > 0 && (
                <span className="text-xs bg-github-red/20 text-github-red px-1.5 py-0.5 rounded-full">{v.at_risk} at risk</span>
              )}
            </div>
          </Card>
        ))}
      </div>

      {/* Chart */}
      <Card title="Ready vs at-risk by team">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#8b949e' }} />
            <YAxis tick={{ fontSize: 12, fill: '#8b949e' }} />
            <Tooltip contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d', color: '#c9d1d9' }} />
            <Legend wrapperStyle={{ color: '#8b949e' }} />
            <Bar dataKey="Ready" fill="#3fb950" radius={[4,4,0,0]} />
            <Bar dataKey="At Risk" fill="#d29922" radius={[4,4,0,0]} />
            <Bar dataKey="Constrained" fill="#8b949e" radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Detail table */}
      <Card title="Team breakdown">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-github-muted text-xs uppercase border-b border-github-border">
            <th className="pb-2 pr-4">Team</th><th className="pb-2 pr-4">Learners</th>
            <th className="pb-2 pr-4">Readiness</th><th className="pb-2 pr-4">Risk rate</th><th className="pb-2">Capacity</th>
          </tr></thead>
          <tbody>
            {teams.map(([name, v]) => (
              <tr key={name} className="border-b border-github-border/30">
                <td className="py-2 pr-4 font-medium text-github-text">{name}</td>
                <td className="py-2 pr-4 text-github-text">{v.learners}</td>
                <td className="py-2 pr-4"><span className={`font-semibold ${v.readiness_rate >= 60 ? 'text-github-green' : 'text-github-yellow'}`}>{v.readiness_rate}%</span></td>
                <td className="py-2 pr-4"><span className={v.risk_rate >= 50 ? 'text-github-red font-semibold' : 'text-github-muted'}>{v.risk_rate}%</span></td>
                <td className="py-2">{v.capacity_constrained > 0 ? <span className="text-github-yellow">{v.capacity_constrained} constrained</span> : <span className="text-github-muted">–</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
