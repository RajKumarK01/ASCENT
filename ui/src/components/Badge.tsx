const variants = {
  green:  'bg-emerald-100 text-emerald-700',
  red:    'bg-red-100 text-red-700',
  amber:  'bg-amber-100 text-amber-700',
  blue:   'bg-blue-100 text-blue-700',
  slate:  'bg-slate-100 text-slate-600',
  purple: 'bg-purple-100 text-purple-700',
}
type V = keyof typeof variants

export function Badge({ label, variant = 'slate' }: { label: string; variant?: V }) {
  return <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${variants[variant]}`}>{label}</span>
}
