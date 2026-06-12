import { useState } from 'react'

const ICONS: Record<string, string> = {
  planner: '🗺',
  concurrent: '⚡',
  'role:curator': '📚',
  'role:engagement': '🔔',
  'role:study_planner': '📅',
  'role:assessment': '✅',
  verifier: '🔍',
  reflect: '🧠',
  'self-reflect': '🔄',
  result: '🎯',
  'tool:microsoft_docs_search': '🔍',
  'tool:microsoft_docs_fetch': '📄',
  'tool:youtube_search': '▶️',
  'tool:error': '⚠️',
}

function stepIcon(line: string) {
  for (const [key, icon] of Object.entries(ICONS)) if (line.includes(`[${key}]`)) return icon
  return '•'
}

function stepColor(line: string) {
  if (line.includes('[verifier]')) return 'border-github-yellow/50 bg-github-yellow/10'
  if (line.includes('[reflect]')) return 'border-purple-500/50 bg-purple-500/10'
  if (line.includes('[self-reflect]')) return 'border-github-purple/50 bg-github-purple/10'
  if (line.includes('READY ->')) return 'border-github-green/50 bg-github-green/10'
  if (line.includes('NOT READY')) return 'border-github-red/50 bg-github-red/10'
  if (line.includes('[concurrent]')) return 'border-github-blue/50 bg-github-blue/10'
  if (line.includes('[tool:')) return 'border-orange-500/50 bg-orange-500/10'
  return 'border-github-border bg-github-surface'
}

export function TraceTimeline({ trace }: { trace: string[] }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mt-2">
      <button onClick={() => setOpen(o => !o)}
        className="text-sm text-github-muted hover:text-github-text flex items-center gap-1 font-medium transition-colors">
        <span className={`transition-transform ${open ? 'rotate-90' : ''}`}>▶</span>
        Reasoning trace ({trace.length} steps)
      </button>
      {open && (
        <div className="mt-3 space-y-2">
          {trace.map((line, i) => (
            <div key={i} className={`flex gap-3 p-2.5 rounded-xl border text-sm ${stepColor(line)}`}>
              <span className="text-base w-6 shrink-0 text-center">{stepIcon(line)}</span>
              <span className="font-mono text-xs text-github-text break-all">{line}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
