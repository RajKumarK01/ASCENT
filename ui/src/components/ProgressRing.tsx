export function ProgressRing({ pct, label, sub }: { pct: number; label: string; sub: string }) {
  const r = 52, circ = 2 * Math.PI * r
  const dash = circ * Math.min(pct / 100, 1)
  const color = pct >= 100 ? '#3fb950' : pct >= 60 ? '#d29922' : '#f85149'
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="128" height="128" viewBox="0 0 128 128">
        <circle cx="64" cy="64" r={r} fill="none" stroke="#30363d" strokeWidth="12" />
        <circle cx="64" cy="64" r={r} fill="none" stroke={color} strokeWidth="12"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
          transform="rotate(-90 64 64)" />
        <text x="64" y="60" textAnchor="middle" className="text-2xl font-bold" fill="#c9d1d9" fontSize="22" fontWeight="700">{Math.round(pct)}%</text>
        <text x="64" y="78" textAnchor="middle" fill="#8b949e" fontSize="11">{label}</text>
      </svg>
      <span className="text-xs text-github-muted">{sub}</span>
    </div>
  )
}
