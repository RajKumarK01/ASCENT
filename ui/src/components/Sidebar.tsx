import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth'

export function Sidebar({ mode }: { mode: string }) {
  const { user, logout } = useAuth()
  const isEmp = user?.role === 'employee'

  const links = isEmp
    ? [{ to: '/', label: 'Dashboard', icon: '🏠' }, { to: '/plan', label: 'Study Plan', icon: '📅' }, { to: '/assessment', label: 'Assessment', icon: '✅' }]
    : [{ to: '/manager', label: 'Team Overview', icon: '📊' }]

  return (
    <aside className="w-56 shrink-0 bg-white border-r border-slate-100 flex flex-col h-screen sticky top-0">
      <div className="p-5 border-b border-slate-100">
        <div className="text-lg font-bold text-slate-800">ASCENT</div>
        <div className="text-xs text-slate-400 mt-0.5">AI Learning Platform</div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {links.map(l => (
          <NavLink key={l.to} to={l.to} end={l.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50'}`}>
            <span>{l.icon}</span>{l.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-slate-100 space-y-2">
        <div className="text-xs text-slate-500 truncate">{user?.name}</div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${isEmp ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}`}>
            {user?.role}
          </span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${mode === 'FOUNDRY' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
            {mode}
          </span>
        </div>
        <button onClick={logout} className="text-xs text-slate-400 hover:text-slate-600">Sign out</button>
      </div>
    </aside>
  )
}
