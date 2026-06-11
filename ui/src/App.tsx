import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import { Sidebar } from './components/Sidebar'
import { Login } from './pages/Login'
import { EmployeeDashboard } from './pages/EmployeeDashboard'
import { StudyPlan } from './pages/StudyPlan'
import { Assessment } from './pages/Assessment'
import { ManagerDashboard } from './pages/ManagerDashboard'
import { api } from './api'

function Shell() {
  const { user, logout } = useAuth()
  const [mode, setMode] = useState('LOCAL')
  useEffect(() => { api.health().then(h => setMode(h.mode)).catch(() => {}) }, [])

  if (!user) return <Navigate to="/login" replace />

  return (
    <div className="flex min-h-screen bg-github-bg">
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
        <Routes>
          <Route path="/login" element={<LoginGate />} />
          <Route path="/*" element={<Shell />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

function LoginGate() {
  const { user } = useAuth()
  if (user) return <Navigate to="/" replace />
  return <Login />
}
