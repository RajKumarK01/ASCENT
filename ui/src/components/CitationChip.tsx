export function CitationChip({ source }: { source: string }) {
  const label = source.startsWith('http') ? source.split('/').pop() ?? source : source
  const isUrl = source.startsWith('http')
  return isUrl
    ? <a href={source} target="_blank" rel="noreferrer"
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-github-blue/20 text-github-blue border border-github-blue/50 hover:bg-github-blue/30 transition-colors">
        <span>&#128196;</span>{label}
      </a>
    : <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-github-blue/20 text-github-blue border border-github-blue/50">
        <span>&#128196;</span>{label}
      </span>
}
