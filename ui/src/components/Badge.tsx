const variants = {
  green:  'bg-github-green/20 text-github-green',
  red:    'bg-github-red/20 text-github-red',
  amber:  'bg-github-yellow/20 text-github-yellow',
  blue:   'bg-github-blue/20 text-github-blue',
  slate:  'bg-github-border/50 text-github-muted',
  purple: 'bg-github-purple/20 text-github-purple',
}
type V = keyof typeof variants

export function Badge({ label, variant = 'slate' }: { label: string; variant?: V }) {
  return <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${variants[variant]}`}>{label}</span>
}
