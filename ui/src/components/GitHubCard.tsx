export function GitHubCard({ title, subtitle, children, className = '' }: { title?: string; subtitle?: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-github-surface rounded-2xl border border-github-border p-5 ${className}`}>
      {(title || subtitle) && (
        <div className="mb-4">
          {title && <h3 className="text-sm font-semibold text-github-text">{title}</h3>}
          {subtitle && <p className="text-xs text-github-muted mt-1">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  )
}
