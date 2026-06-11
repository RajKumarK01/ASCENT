import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import { PlanProvider, usePlan } from './context/PlanContext'
import { Sidebar } from './components/Sidebar'
import { PathSetupModal } from './components/PathSetupModal'
import { Login } from './pages/Login'
import { EmployeeDashboard } from './pages/EmployeeDashboard'
import { StudyPlan } from './pages/StudyPlan'
import { Assessment } from './pages/Assessment'
import { ManagerDashboard } from './pages/ManagerDashboard'
import { api } from './api'

function Shell() {
  const { user } = useAuth()
  const { refresh, clearPlan } = usePlan()
  const [mode, setMode] = useState('LOCAL')
  const [profile, setProfile] = useState<any>(null)
  const [showSetup, setShowSetup] = useState(false)

  useEffect(() => { api.health().then(h => setMode(h.mode)).catch(() => {}) }, [])

  useEffect(() => {
    if (user?.role === 'employee') {
      // Load profile immediately (fast, no AI) to decide whether to show setup modal
      api.profile().then(p => {
        setProfile(p)
        if (p?.needs_selection) setShowSetup(true)
        else refresh()  // start loading plan in background
      }).catch(() => refresh())
    }
  }, [user])

  if (!user) return <Navigate to="/login" replace />

  async function handlePathConfirm(path: string, cert: string) {
    await api.updateProfile({ path, certification: cert })
    const p = await api.profile()
    setProfile(p)
    setShowSetup(false)
    clearPlan()
    refresh()
  }

  return (
    <div className="flex min-h-screen bg-github-bg">
      {showSetup && profile && (
        <PathSetupModal
          profile={profile}
          onConfirm={handlePathConfirm}
          onDismiss={() => { setShowSetup(false); refresh() }}
        />
      )}
      <Sidebar mode={mode} />
      <main className="min-h-0 flex-1 overflow-auto">
        <Routes>
          {user.role === 'employee' ? (
            <>
              <Route path="/" element={<EmployeeDashboard />} />
              <Route path="/plan" element={<StudyPlan />} />
              <Route path="/assessment" element={<Assessment />} />
            </>
          ) : (
            <Route path="/manager" element={<ManagerDashboard />} />
          )}
          <Route path="*" element={<Navigate to={user.role === 'manager' ? '/manager' : '/'} replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <PlanProvider>
          <Routes>
            <Route path="/login" element={<LoginGate />} />
            <Route path="/*" element={<Shell />} />
          </Routes>
        </PlanProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}

function LoginGate() {
  const { user } = useAuth()
  if (user) return <Navigate to="/" replace />
  return <Login />
}
