import { useState } from 'react'

const ICONS: Record<string, string> = {
  planner: '🗺',
  concurrent: '⚡',
  'role:curator': '📚',
  'role:engagement': '🔔',
  'role:study_planner': '📅',
  'role:assessment': '✅',
  verifier: '🔍',
  'self-reflect': '🔄',
  result: '🎯',
}

function stepIcon(line: string) {
  for (const [key, icon] of Object.entries(ICONS)) if (line.includes(`[${key}]`)) return icon
  return '•'
}

function stepColor(line: string) {
  if (line.includes('[verifier]')) return 'border-amber-400 bg-amber-50'
  if (line.includes('[self-reflect]')) return 'border-purple-400 bg-purple-50'
  if (line.includes('READY ->')) return 'border-emerald-400 bg-emerald-50'
  if (line.includes('NOT READY')) return 'border-red-400 bg-red-50'
  if (line.includes('[concurrent]')) return 'border-blue-400 bg-blue-50'
  return 'border-slate-200 bg-white'
}

export function TraceTimeline({ trace }: { trace: string[] }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-2">
      <button onClick={() => setOpen(o => !o)}
        className="text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1 font-medium">
        <span className={`transition-transform ${open ? 'rotate-90' : ''}`}>▶</span>
        Reasoning trace ({trace.length} steps)
      </button>
      {open && (
        <div className="mt-3 space-y-2">
          {trace.map((line, i) => (
            <div key={i} className={`flex gap-3 p-2.5 rounded-xl border text-sm ${stepColor(line)}`}>
              <span className="text-base w-6 shrink-0 text-center">{stepIcon(line)}</span>
              <span className="font-mono text-xs text-slate-700 break-all">{line}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
