import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { CitationChip } from '../components/CitationChip'

export function StudyPlan() {
  const [data, setData] = useState<any>(null)
  const [weeks, setWeeks] = useState(4)
  const [loading, setLoading] = useState(true)

  async function load(w: number) {
    setLoading(true)
    try { setData(await api.plan(w)) } finally { setLoading(false) }
  }
  useEffect(() => { load(weeks) }, [])

  const plan = data?.study_plan
  const cur  = data?.curator

  return (
    <div className="p-6 space-y-5 max-w-3xl">
      <h1 className="text-2xl font-bold text-slate-800">Study Plan</h1>

      {loading && <div className="text-slate-400">Loading…</div>}
      {!loading && plan && (
        <>
          <Card>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div><div className="text-slate-500">Total hours</div><div className="text-xl font-bold text-slate-800 mt-1">{plan.total_recommended_hours}h</div></div>
              <div><div className="text-slate-500">Duration</div><div className="text-xl font-bold text-slate-800 mt-1">{plan.weeks} weeks</div></div>
              <div><div className="text-slate-500">Hours / week</div><div className="text-xl font-bold text-slate-800 mt-1">{plan.hours_per_week}h</div></div>
            </div>
            {plan.prerequisites?.length > 0 && (
              <div className="mt-3 text-sm"><span className="text-slate-500">Prerequisites: </span>
                {plan.prerequisites.map((p: string) => <Badge key={p} label={p} variant="amber" />)}
              </div>
            )}
          </Card>

          <Card title="Milestones">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-slate-400 text-xs uppercase border-b border-slate-100">
                <th className="pb-2 pr-4">Week</th><th className="pb-2 pr-4">Skill</th><th className="pb-2 pr-4">Hours</th><th className="pb-2">Status</th>
              </tr></thead>
              <tbody>
                {plan.milestones?.map((m: any, i: number) => (
                  <tr key={i} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="py-2 pr-4 font-medium text-slate-700">{m.week}</td>
                    <td className="py-2 pr-4 text-slate-800">{m.focus_skill}</td>
                    <td className="py-2 pr-4 text-slate-600">{m.target_hours}h</td>
                    <td className="py-2"><Badge label={m.is_gap ? 'Gap' : 'Reinforce'} variant={m.is_gap ? 'red' : 'slate'} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {cur?.citations?.length > 0 && (
            <Card title="Knowledge sources">
              <div className="flex flex-wrap gap-2">
                {[...new Set(cur.citations as string[])].map((c: string) => <CitationChip key={c} source={c} />)}
              </div>
            </Card>
          )}

          <div className="flex items-center gap-3">
            <label className="text-sm text-slate-600">Adjust weeks:</label>
            {[4,6,8,12].map(w => (
              <button key={w} onClick={() => { setWeeks(w); load(w) }}
                className={`px-3 py-1 rounded-lg text-sm font-medium border transition-colors ${weeks===w ? 'bg-indigo-600 text-white border-indigo-600' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`}>
                {w}w
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
