import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import { api } from '../api'
import type { ContributionData } from '../components/ContributionHeatmap'

interface PlanState {
  data: any | null
  contributions: ContributionData
  loading: boolean
  error: string
  weeks: number
  setWeeks: (w: number) => void
  refresh: (w?: number) => Promise<void>
  clearPlan: () => void
}

const Ctx = createContext<PlanState>(null!)
export const usePlan = () => useContext(Ctx)

export function PlanProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<any>(null)
  const [contributions, setContributions] = useState<ContributionData>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [weeks, setWeeksState] = useState(4)

  const refresh = useCallback(async (w?: number) => {
    const targetWeeks = w ?? weeks
    setLoading(true)
    setError('')
    try {
      const [planData, contribData] = await Promise.race([
        Promise.all([api.plan(targetWeeks), api.contributions()]),
        new Promise<never>((_, reject) => setTimeout(() => reject(new Error('timeout')), 180000)),
      ]) as [any, ContributionData]
      setData(planData)
      setContributions(contribData)
    } catch (ex: any) {
      setError(ex.message === 'timeout' ? 'Plan generation timed out (AI agents are busy). Please retry.' : ex.message ?? 'Error loading plan.')
    } finally {
      setLoading(false)
    }
  }, [weeks])

  const setWeeks = useCallback((w: number) => {
    setWeeksState(w)
    refresh(w)
  }, [refresh])

  function clearPlan() {
    setData(null)
    setContributions({})
    setError('')
  }

  return (
    <Ctx.Provider value={{ data, contributions, loading, error, weeks, setWeeks, refresh, clearPlan }}>
      {children}
    </Ctx.Provider>
  )
}
