import { createContext, useContext, useState, ReactNode } from 'react'
import { api, setToken } from './api'

interface User { email: string; name: string; role: string; scope: string }
interface AuthCtx { user: User | null; login: (e: string, p: string) => Promise<void>; logout: () => void }

const Ctx = createContext<AuthCtx>(null!)
export const useAuth = () => useContext(Ctx)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)

  async function login(email: string, password: string) {
    const data = await api.login(email, password)
    setToken(data.access_token)
    setUser({ email: data.email, name: data.name, role: data.role, scope: data.scope })
  }

  function logout() {
    setToken(null)
    setUser(null)
  }

  return <Ctx.Provider value={{ user, login, logout }}>{children}</Ctx.Provider>
}
