import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card } from '../components/Card'
import { Badge } from '../components/Badge'
import { CitationChip } from '../components/CitationChip'

export function Assessment() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [answers, setAnswers] = useState<Record<number, number>>({})
  const [submitted, setSubmitted] = useState(false)
  const [score, setScore] = useState(0)

  useEffect(() => {
    api.assessment().then(setData).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-github-muted">Loading assessment…</div>
  if (!data) return null

  const r = data.readiness ?? {}
  const questions = data.questions ?? []
  const percentage = questions.length ? Math.round((score / questions.length) * 100) : 0
  const readinessImpact = Math.max(0, percentage - 70)
  const strongAreas = Array.from(new Set(questions.filter((q: any, idx: number) => answers[idx] === q.correct_index).map((q: any) => q.skill)))
  const weakAreas = Array.from(new Set(questions.filter((q: any, idx: number) => answers[idx] != null && answers[idx] !== q.correct_index).map((q: any) => q.skill)))
  const attemptCount = 1 + (data.loops ?? 0)
  const lastAssessmentDate = data.last_assessment_date ?? new Date().toLocaleDateString()

  function selectAnswer(questionIndex: number, choiceIndex: number) {
    if (submitted) return
    setAnswers(prev => ({ ...prev, [questionIndex]: choiceIndex }))
  }

  function submitAnswers() {
    const correct = questions.reduce((count: number, q: any, idx: number) => {
      return count + ((answers[idx] === q.correct_index) ? 1 : 0)
    }, 0)
    setScore(correct)
    setSubmitted(true)
  }

  return (
    <div className="p-6 space-y-5 max-w-4xl mx-auto">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-github-text">Assessment</h1>
          <p className="text-sm text-github-muted mt-1">Practice questions grounded in your selected certification journey.</p>
        </div>
        <Badge label={data.all_questions_cited ? 'All cited' : 'Uncited questions'} variant={data.all_questions_cited ? 'green' : 'red'} />
      </div>

      <Card title="Readiness verdict">
        <div className="grid gap-4 sm:grid-cols-2 text-sm">
          <div>
            <div className="text-github-muted">Status</div>
            <div className="mt-2"><Badge label={r.ready ? 'READY' : 'NOT READY'} variant={r.ready ? 'green' : 'amber'} /></div>
          </div>
          <div>
            <div className="text-github-muted">Pass threshold</div>
            <div className="mt-2 font-medium text-github-text">{r.pass_threshold}%</div>
          </div>
          {r.score_gap > 0 && (
            <div>
              <div className="text-github-muted">Score gap</div>
              <div className="mt-2 font-medium text-github-red">+{r.score_gap}% needed</div>
            </div>
          )}
          {r.hours_gap > 0 && (
            <div>
              <div className="text-github-muted">Hours gap</div>
              <div className="mt-2 font-medium text-github-red">{r.hours_gap}h more needed</div>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="text-sm text-github-muted">Question bank</div>
            <div className="mt-1 text-lg font-semibold text-github-text">{questions.length} questions</div>
          </div>
          <div className="text-right text-sm text-github-muted">
            <div>Last assessed</div>
            <div className="mt-1 text-github-text">{lastAssessmentDate}</div>
            <div className="mt-2">Attempts: {attemptCount}</div>
          </div>
        </div>
      </Card>

      <Card title="Practice questions">
        {questions.length === 0 ? (
          <div className="text-sm text-github-muted italic">No grounded questions available — knowledge base returned no content for these skills.</div>
        ) : (
          <div className="space-y-5">
            {questions.map((q: any, i: number) => {
              const selected = answers[i]
              const isWrong = submitted && selected != null && selected !== q.correct_index

              return (
                <div key={i} className="rounded-3xl border border-github-border bg-github-surface p-5">
                  <div className="flex flex-col gap-3">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="text-sm text-github-muted">Question {i + 1} of {questions.length}</div>
                      <div className="flex flex-wrap gap-2">
                        <Badge label={q.skill} variant="blue" />
                        {q.citations?.length > 0 && <Badge label="Cited" variant="green" />}
                      </div>
                    </div>
                    <p className="text-lg font-semibold text-github-text">{q.question}</p>

                    <div className="grid gap-3">
                      {q.choices.map((choice: string, idx: number) => {
                        const active = selected === idx
                        const correctChoice = submitted && idx === q.correct_index
                        return (
                          <button key={idx} type="button"
                            onClick={() => selectAnswer(i, idx)}
                            onKeyDown={e => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault()
                                selectAnswer(i, idx)
                              }
                            }}
                            className={`w-full rounded-3xl border px-4 py-4 text-left transition ${active ? 'border-github-blue bg-github-blue/10 shadow-sm' : 'border-github-border bg-github-bg hover:border-github-blue/60 hover:bg-github-border/20'} ${submitted ? (correctChoice ? 'border-github-green bg-github-green/10' : isWrong && active ? 'border-github-red bg-github-red/10' : '') : ''}`}>
                            <div className={`text-sm ${active ? 'font-semibold text-github-text' : 'text-github-text'}`}><span className="mr-3">{String.fromCharCode(65 + idx)}.</span>{choice}</div>
                          </button>
                        )
                      })}
                    </div>

                    {q.hint && <div className="rounded-2xl bg-github-border/10 px-4 py-3 text-sm text-github-muted">Hint: {q.hint}</div>}
                    {q.citations?.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {[...new Set(q.citations as string[])].map((c: string) => <CitationChip key={c} source={c} />)}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <button type="button" onClick={submitAnswers}
                className="rounded-2xl bg-github-blue px-5 py-3 text-sm font-semibold text-github-bg transition hover:bg-github-blue/80">
                Submit answers
              </button>
              {submitted && (
                <div className="text-sm text-github-muted">Score: <span className="font-semibold text-github-text">{score}/{questions.length}</span></div>
              )}
            </div>
          </div>
        )}
      </Card>

      {submitted && (
        <Card title="Assessment result">
          <div className="grid gap-6 md:grid-cols-2">
            <div className="rounded-3xl border border-github-border bg-github-bg p-4">
              <div className="text-sm text-github-muted">Score</div>
              <div className="mt-2 text-3xl font-semibold text-github-text">{score}/{questions.length}</div>
              <div className="mt-2 text-sm text-github-muted">Percentage: {percentage}%</div>
            </div>
            <div className="rounded-3xl border border-github-border bg-github-bg p-4">
              <div className="text-sm text-github-muted">Readiness impact</div>
              <div className="mt-2 text-3xl font-semibold text-github-text">+{readinessImpact}%</div>
              <div className="mt-2 text-sm text-github-muted">Based on answering the current set of questions.</div>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2 mt-6">
            <div>
              <div className="text-sm text-github-muted">Strong areas</div>
              <div className="mt-3 space-y-2">
                {strongAreas.length ? (strongAreas as string[]).map(area => (
                  <div key={area} className="rounded-2xl border border-github-border bg-github-bg px-4 py-3 text-sm text-github-text">{area}</div>
                )) : <div className="text-sm text-github-muted">Keep practicing to identify your strengths.</div>}
              </div>
            </div>
            <div>
              <div className="text-sm text-github-muted">Weak areas</div>
              <div className="mt-3 space-y-2">
                {weakAreas.length ? (weakAreas as string[]).map(area => (
                  <div key={area} className="rounded-2xl border border-github-border bg-github-bg px-4 py-3 text-sm text-github-text">{area}</div>
                )) : <div className="text-sm text-github-muted">No weak areas detected yet.</div>}
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
