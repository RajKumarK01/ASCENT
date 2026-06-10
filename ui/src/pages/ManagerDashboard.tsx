import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card } from '../components/Card'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export function ManagerDashboard() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')

  useEffect(() => { api.insights().then(setData).catch(e => setErr(e.message)).finally(() => setLoading(false)) }, [])

  if (loading) return <div className="p-8 text-slate-400">Loading team insights…</div>
  if (err) return <div className="p-8 text-red-600">{err}</div>
  if (!data) return null

  const teams = Object.entries(data.teams ?? {}) as [string, any][]
  const chartData = teams.map(([name, v]) => ({
    name, Ready: v.ready, 'At Risk': v.at_risk, Constrained: v.capacity_constrained,
  }))

  return (
    <div className="p-6 space-y-5 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Team Overview</h1>
        <p className="text-slate-500 text-sm mt-1">Scope: {data.scope}</p>
      </div>

      {/* Privacy note */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-xs text-blue-700 flex items-start gap-2">
        <span>🔒</span>
        <span>This view shows aggregate team data only. No individual learner schedules, IDs, or personal details are exposed.</span>
      </div>

      {/* KPI tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {teams.map(([name, v]) => (
          <Card key={name} className="text-center">
            <div className="text-xs text-slate-500 mb-1">{name}</div>
            <div className="text-2xl font-bold text-slate-800">{v.readiness_rate}%</div>
            <div className="text-xs text-slate-500">ready</div>
            <div className="mt-2 flex justify-center gap-1 flex-wrap">
              {v.capacity_constrained > 0 && (
                <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">{v.capacity_constrained} constrained</span>
              )}
              {v.at_risk > 0 && (
                <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full">{v.at_risk} at risk</span>
              )}
            </div>
          </Card>
        ))}
      </div>

      {/* Chart */}
      <Card title="Ready vs at-risk by team">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="Ready" fill="#10b981" radius={[4,4,0,0]} />
            <Bar dataKey="At Risk" fill="#f59e0b" radius={[4,4,0,0]} />
            <Bar dataKey="Constrained" fill="#94a3b8" radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Detail table */}
      <Card title="Team breakdown">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-slate-400 text-xs uppercase border-b border-slate-100">
            <th className="pb-2 pr-4">Team</th><th className="pb-2 pr-4">Learners</th>
            <th className="pb-2 pr-4">Readiness</th><th className="pb-2 pr-4">Risk rate</th><th className="pb-2">Capacity</th>
          </tr></thead>
          <tbody>
            {teams.map(([name, v]) => (
              <tr key={name} className="border-b border-slate-50">
                <td className="py-2 pr-4 font-medium text-slate-700">{name}</td>
                <td className="py-2 pr-4">{v.learners}</td>
                <td className="py-2 pr-4"><span className={`font-semibold ${v.readiness_rate >= 60 ? 'text-emerald-600' : 'text-amber-600'}`}>{v.readiness_rate}%</span></td>
                <td className="py-2 pr-4"><span className={v.risk_rate >= 50 ? 'text-red-600 font-semibold' : 'text-slate-600'}>{v.risk_rate}%</span></td>
                <td className="py-2">{v.capacity_constrained > 0 ? <span className="text-amber-600">{v.capacity_constrained} constrained</span> : <span className="text-slate-400">–</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
