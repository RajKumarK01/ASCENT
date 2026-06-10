import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { CitationChip } from '../components/CitationChip'
import { LoadingScreen } from '../components/LoadingScreen'

export function Assessment() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { api.assessment().then(setData).finally(() => setLoading(false)) }, [])

  if (loading) return <LoadingScreen />
  if (!data) return null

  const r = data.readiness ?? {}

  return (
    <div className="p-6 space-y-5 max-w-3xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Assessment</h1>
        <Badge label={data.all_questions_cited ? 'All cited' : 'Uncited questions'} variant={data.all_questions_cited ? 'green' : 'red'} />
      </div>

      <Card title="Readiness verdict">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-slate-500">Status</span>
            <div className="mt-1"><Badge label={r.ready ? 'READY' : 'NOT READY'} variant={r.ready ? 'green' : 'amber'} /></div>
          </div>
          <div><span className="text-slate-500">Pass threshold</span><div className="font-medium mt-1">{r.pass_threshold}%</div></div>
          {r.score_gap > 0 && <div><span className="text-slate-500">Score gap</span><div className="font-medium text-red-600 mt-1">+{r.score_gap}% needed</div></div>}
          {r.hours_gap > 0 && <div><span className="text-slate-500">Hours gap</span><div className="font-medium text-red-600 mt-1">{r.hours_gap}h more needed</div></div>}
        </div>
      </Card>

      <Card title="Practice questions">
        {data.questions?.length === 0
          ? <div className="text-sm text-slate-500 italic">No grounded questions available — knowledge base returned no content for these skills.</div>
          : <div className="space-y-4">
              {data.questions?.map((q: any, i: number) => (
                <div key={i} className="border border-slate-100 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge label={q.skill} variant="blue" />
                    {q.citations?.length > 0 && <Badge label="Cited" variant="green" />}
                  </div>
                  <p className="text-sm text-slate-800 font-medium">{q.question}</p>
                  {q.citations?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {[...new Set(q.citations as string[])].map((c: string) => <CitationChip key={c} source={c} />)}
                    </div>
                  )}
                </div>
              ))}
            </div>
        }
      </Card>
    </div>
  )
}
