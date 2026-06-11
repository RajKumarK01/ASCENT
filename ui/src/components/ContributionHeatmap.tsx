import { useState } from 'react'

export interface ContributionData {
  [dateStr: string]: number  // e.g., "2025-06-10": 2
}

interface Tooltip {
  x: number
  y: number
  date: string
  count: number
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function getColor(count: number): string {
  if (count === 0) return '#161b22'
  if (count === 1) return '#0e4429'
  if (count === 2) return '#006d32'
  if (count === 3) return '#26a641'
  return '#39d353'
}

export function ContributionHeatmap({ data, loading = false }: { data: ContributionData; loading?: boolean }) {
  const [tooltip, setTooltip] = useState<Tooltip | null>(null)

  const today = new Date()
  const days: Date[] = []
  for (let i = 364; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    days.push(d)
  }

  const weeks: Date[][] = []
  let currentWeek: Date[] = []
  const firstDay = days[0]
  const startDayOfWeek = firstDay.getDay()
  for (let i = startDayOfWeek - 1; i >= 0; i--) {
    const pad = new Date(firstDay)
    pad.setDate(pad.getDate() - (startDayOfWeek - i))
    currentWeek.unshift(pad)
  }

  for (const day of days) {
    currentWeek.push(day)
    if (currentWeek.length === 7) {
      weeks.push([...currentWeek])
      currentWeek = []
    }
  }
  if (currentWeek.length > 0) {
    weeks.push([...currentWeek])
  }

  const monthLabels: { week: number; label: string }[] = []
  let lastMonth = -1
  weeks.forEach((week, idx) => {
    const month = week[0]?.getMonth() ?? 0
    if (month !== lastMonth) {
      monthLabels.push({ week: idx, label: MONTHS[month] })
      lastMonth = month
    }
  })

  const dateStr = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

  return (
    <div className="relative w-full min-w-0">
      {loading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-[#0d1117]/50">
          <span className="text-github-muted">Loading…</span>
        </div>
      )}

      <div className="w-full overflow-x-auto">
        <div className="mb-3 flex items-center gap-2 pl-9">
          <span className="text-xs text-github-muted">Less</span>
          {[0, 1, 2, 3].map(i => (
            <div key={i} className="h-3 w-3 rounded-sm" style={{ backgroundColor: getColor(i) }} title={`${i}${i > 0 ? ' tasks' : ' activity'}`} />
          ))}
          <span className="text-xs text-github-muted">More</span>
        </div>

        <div className="flex min-w-0 gap-[3px]">
          <div className="flex shrink-0 flex-col gap-[3px] pt-5">
            {[1, 3, 5].map(dayIdx => (
              <div key={dayIdx} className="flex h-3 w-7 items-center justify-end pr-1">
                <span className="text-[10px] text-github-muted">{WEEKDAYS[dayIdx]}</span>
              </div>
            ))}
          </div>

          <div className="grid gap-[3px]" style={{ gridAutoFlow: 'column' }}>
            {weeks.map((week, weekIdx) => (
              <div key={weekIdx} className="grid gap-[3px]" style={{ gridTemplateRows: '12px repeat(7, 12px)' }}>
                <div className="flex h-3 items-center">
                  {monthLabels.find(m => m.week === weekIdx) && (
                    <span className="whitespace-nowrap text-[10px] font-semibold text-github-muted">
                      {monthLabels.find(m => m.week === weekIdx)?.label}
                    </span>
                  )}
                </div>
                {week.map((day, dayIdx) => {
                  const ds = dateStr(day)
                  const count = data[ds] ?? 0
                  const isPast = day <= today
                  return (
                    <div
                      key={`${weekIdx}-${dayIdx}`}
                      className="h-3 w-3 shrink-0 cursor-pointer rounded-sm border border-[#30363d]/30 transition-colors hover:border-github-blue"
                      style={{ backgroundColor: isPast ? getColor(count) : '#0d1117' }}
                      onMouseEnter={(e) => {
                        if (isPast) {
                          const rect = e.currentTarget.getBoundingClientRect()
                          setTooltip({ x: rect.left, y: rect.top, date: ds, count })
                        }
                      }}
                      onMouseLeave={() => setTooltip(null)}
                      title={`Completed ${count} learning activit${count === 1 ? 'y' : 'ies'} on ${day.toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })}`}
                    />
                  )
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {tooltip && (
        <div
          className="pointer-events-none fixed z-50 rounded-lg border border-[#30363d] bg-[#161b22] px-3 py-2 text-xs text-github-text shadow-lg"
          style={{ left: `${tooltip.x}px`, top: `${tooltip.y - 44}px` }}
        >
          <div className="font-semibold">Completed {tooltip.count} learning activit{tooltip.count === 1 ? 'y' : 'ies'}</div>
          <div className="text-github-muted">{new Date(tooltip.date).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' })}</div>
        </div>
      )}
    </div>
  )
}
