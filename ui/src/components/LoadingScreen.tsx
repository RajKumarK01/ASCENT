import { useEffect, useState } from 'react'

const STEPS = [
  { icon: '🗺', label: 'Planning your learning route…',             agent: 'Orchestrator' },
  { icon: '📚', label: 'Curating certified learning content…',      agent: 'Curator Agent + Microsoft Learn MCP' },
  { icon: '🔔', label: 'Analysing your work rhythm…',               agent: 'Engagement Agent' },
  { icon: '📅', label: 'Building your personalised study plan…',    agent: 'Study Planner Agent' },
  { icon: '✅', label: 'Generating grounded practice questions…',   agent: 'Assessment Agent' },
  { icon: '🔍', label: 'Verifying readiness & citations…',          agent: 'Critic / Verifier' },
]

export function LoadingScreen() {
  const [activeStep, setActiveStep] = useState(0)
  const [dots, setDots]             = useState('.')

  useEffect(() => {
    const stepTimer = setInterval(() => {
      setActiveStep(s => Math.min(s + 1, STEPS.length - 1))
    }, 7000)
    const dotTimer = setInterval(() => {
      setDots(d => d.length >= 3 ? '.' : d + '.')
    }, 500)
    return () => { clearInterval(stepTimer); clearInterval(dotTimer) }
  }, [])

  return (
    <div className="flex min-h-screen items-center justify-center bg-github-bg p-6">
      <div className="w-full max-w-md">

        <div className="mb-10 text-center">
          <div className="text-4xl font-bold text-github-text mb-1">ASCENT</div>
          <div className="text-github-muted text-sm">
            AI agents are generating your personalised learning plan{dots}
          </div>
          <div className="mt-3 inline-block rounded-full border border-github-blue/30 bg-github-blue/10 px-3 py-1 text-xs font-medium text-github-blue">
            Powered by Azure AI Foundry · GPT-4.1
          </div>
        </div>

        <div className="space-y-3">
          {STEPS.map((step, i) => {
            const done   = i < activeStep
            const active = i === activeStep
            return (
              <div key={i}
                className={`flex items-center gap-3 rounded-xl border px-4 py-3 transition-all duration-500 ${
                  done    ? 'border-github-green/30 bg-github-green/5 opacity-60' :
                  active  ? 'border-github-blue/50 bg-github-surface shadow-lg scale-[1.01]' :
                            'border-github-border bg-github-surface opacity-25'
                }`}>

                <div className="w-8 h-8 flex items-center justify-center shrink-0">
                  {done   ? <span className="text-github-green text-lg">✓</span> :
                   active ? <Spinner /> :
                            <span className="text-github-muted text-lg">{step.icon}</span>}
                </div>

                <div className="flex-1 min-w-0">
                  <div className={`text-sm font-medium ${
                    active ? 'text-github-text' : done ? 'text-github-muted' : 'text-github-muted'
                  }`}>
                    {step.label}
                  </div>
                  <div className="text-xs text-github-muted mt-0.5">{step.agent}</div>
                </div>

                {active && (
                  <div className="flex gap-1 shrink-0">
                    {[0,1,2].map(j => (
                      <div key={j}
                        className="w-1.5 h-1.5 rounded-full bg-github-blue animate-bounce"
                        style={{ animationDelay: `${j * 0.15}s` }} />
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        <p className="mt-8 text-center text-xs text-github-muted">
          Responses are grounded in your knowledge base and cited · Foundry mode may take 30–60s
        </p>
      </div>
    </div>
  )
}

function Spinner() {
  return (
    <svg className="h-5 w-5 animate-spin text-github-blue" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}
