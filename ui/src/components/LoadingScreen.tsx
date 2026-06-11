import { useEffect, useState } from 'react'

const STEPS = [
  { icon: '🗺', label: 'Planning your learning route…',        agent: 'Orchestrator' },
  { icon: '📚', label: 'Curating certified learning content…', agent: 'Curator Agent' },
  { icon: '🔔', label: 'Analysing your work rhythm…',          agent: 'Engagement Agent' },
  { icon: '📅', label: 'Building your study milestones…',      agent: 'Study Planner Agent' },
  { icon: '✅', label: 'Generating grounded practice questions…', agent: 'Assessment Agent' },
  { icon: '🔍', label: 'Verifying readiness & citations…',     agent: 'Critic / Verifier' },
]

export function LoadingScreen() {
  const [activeStep, setActiveStep] = useState(0)
  const [dots, setDots]             = useState('.')

  useEffect(() => {
    const stepTimer = setInterval(() => {
      setActiveStep(s => (s + 1) % STEPS.length)
    }, 2200)
    const dotTimer = setInterval(() => {
      setDots(d => d.length >= 3 ? '.' : d + '.')
    }, 500)
    return () => { clearInterval(stepTimer); clearInterval(dotTimer) }
  }, [])

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-indigo-50 via-white to-slate-100 flex items-center justify-center z-50">
      <div className="max-w-md w-full px-8">

        {/* Logo & title */}
        <div className="text-center mb-10">
          <div className="text-4xl font-bold text-slate-800 mb-1">ASCENT</div>
          <div className="text-slate-500 text-sm">AI is generating your personalised learning plan{dots}</div>
          <div className="mt-2 inline-block px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs font-medium">
            Powered by Azure AI Foundry · GPT-4.1
          </div>
        </div>

        {/* Animated steps */}
        <div className="space-y-3">
          {STEPS.map((step, i) => {
            const done   = i < activeStep
            const active = i === activeStep
            return (
              <div key={i}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-all duration-500 ${
                  done    ? 'bg-emerald-50 border-emerald-200 opacity-60' :
                  active  ? 'bg-white border-indigo-300 shadow-md scale-[1.02]' :
                            'bg-white border-slate-100 opacity-30'
                }`}>

                {/* Icon / spinner / tick */}
                <div className="w-8 h-8 flex items-center justify-center shrink-0">
                  {done   ? <span className="text-emerald-500 text-lg">✓</span> :
                   active ? <Spinner /> :
                            <span className="text-slateink-300 text-lg">{step.icon}</span>}
                </div>

                <div className="flex-1 min-w-0">
                  <div className={`text-sm font-medium ${active ? 'text-indigo-700' : done ? 'text-slate-400' : 'text-slate-400'}`}>
                    {step.label}
                  </div>
                  <div className="text-xs text-slate-400 mt-0.5">{step.agent}</div>
                </div>

                {active && (
                  <div className="flex gap-1 shrink-0">
                    {[0,1,2].map(j => (
                      <div key={j}
                        className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"
                        style={{ animationDelay: `${j * 0.15}s` }} />
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-slate-400 mt-8">
          Responses are grounded in your knowledge base and cited — this takes 10–15 seconds.
        </p>
      </div>
    </div>
  )
}

function Spinner() {
  return (
    <svg className="animate-spin w-5 h-5 text-indigo-500" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}
