export function Card({ title, children, className = '' }: { title?: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-[#30363d] bg-[#161b22] p-6 shadow-sm ${className}`}>
      {title && <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-github-muted">{title}</h3>}
      {children}
    </div>
  )
}
