import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth'

export function Sidebar({ mode }: { mode: string }) {
  const { user, logout } = useAuth()
  const isEmp = user?.role === 'employee'

  const links = isEmp
    ? [{ to: '/', label: 'Dashboard', icon: '🏠' }, { to: '/plan', label: 'Study Plan', icon: '📅' }, { to: '/assessment', label: 'Assessment', icon: '✅' }]
    : [{ to: '/manager', label: 'Team Overview', icon: '📊' }]

  return (
    <aside className="w-56 shrink-0 bg-github-surface border-r border-github-border flex flex-col h-screen sticky top-0">
      <div className="p-5 border-b border-github-border">
        <div className="text-lg font-bold text-github-text">ASCENT</div>
        <div className="text-xs text-github-muted mt-0.5">AI Learning Platform</div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {links.map(l => (
          <NavLink key={l.to} to={l.to} end={l.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${isActive ? 'bg-github-blue/20 text-github-blue' : 'text-github-muted hover:bg-github-border/30 hover:text-github-text'}`}>
            <span>{l.icon}</span>{l.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-github-border space-y-2">
        <div className="text-xs text-github-muted truncate">{user?.name}</div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${isEmp ? 'bg-github-blue/20 text-github-blue' : 'bg-github-greenMed/20 text-github-greenMed'}`}>
            {user?.role}
          </span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${mode === 'FOUNDRY' ? 'bg-github-green/20 text-github-green' : 'bg-github-border/50 text-github-muted'}`}>
            {mode}
          </span>
        </div>
        <button onClick={logout} className="text-xs text-github-muted hover:text-github-text transition-colors">Sign out</button>
      </div>
    </aside>
  )
}
