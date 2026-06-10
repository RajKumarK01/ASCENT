export function ProgressRing({ pct, label, sub }: { pct: number; label: string; sub: string }) {
  const r = 52, circ = 2 * Math.PI * r
  const dash = circ * Math.min(pct / 100, 1)
  const color = pct >= 100 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#ef4444'
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="128" height="128" viewBox="0 0 128 128">
        <circle cx="64" cy="64" r={r} fill="none" stroke="#e2e8f0" strokeWidth="12" />
        <circle cx="64" cy="64" r={r} fill="none" stroke={color} strokeWidth="12"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          transform="rotate(-90 64 64)" />
        <text x="64" y="60" textAnchor="middle" className="text-2xl font-bold" fill="#1e293b" fontSize="22" fontWeight="700">{Math.round(pct)}%</text>
        <text x="64" y="78" textAnchor="middle" fill="#64748b" fontSize="11">{label}</text>
      </svg>
      <span className="text-xs text-slate-500">{sub}</span>
    </div>
  )
}
