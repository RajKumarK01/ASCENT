import { useState } from 'react'
import { api } from '../api'

export function StudyCheckinButton({ 
  onSuccess, 
  disabled = false,
  todayCompleted = false 
}: { 
  onSuccess?: () => void
  disabled?: boolean
  todayCompleted?: boolean 
}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleCheckin() {
    if (loading || disabled || todayCompleted) return
    
    setLoading(true)
    setError('')
    
    try {
      await api.studyCheckin()
      onSuccess?.()
    } catch (e: any) {
      setError(e.message || 'Failed to mark study as completed')
      setLoading(false)
    }
  }

  const isDisabled = disabled || todayCompleted || loading

  return (
    <div className="flex flex-col gap-2">
      <button
        onClick={handleCheckin}
        disabled={isDisabled}
        className={`px-4 py-2.5 rounded-xl font-medium text-sm transition-colors flex items-center gap-2 justify-center ${
          todayCompleted
            ? 'bg-github-green/20 text-github-green border border-github-green/50 cursor-not-allowed'
            : isDisabled
            ? 'bg-github-border/30 text-github-muted cursor-not-allowed opacity-50'
            : 'bg-github-green hover:bg-github-green/80 text-github-bg'
        }`}
      >
        {loading ? (
          <>
            <span className="animate-spin">⏳</span>
            Marking…
          </>
        ) : todayCompleted ? (
          <>
            <span>✓</span>
            Today marked completed
          </>
        ) : (
          <>
            <span>✓</span>
            Mark today as completed
          </>
        )}
      </button>
      
      {error && (
        <div className="text-xs text-github-red bg-github-red/10 rounded-lg px-3 py-2 border border-github-red/20">
          {error}
        </div>
      )}
    </div>
  )
}
