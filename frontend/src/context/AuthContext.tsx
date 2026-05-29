import { createContext, useCallback, useContext, useEffect, useState } from "react"
import { api, ApiError } from "@/lib/api"

type User = { id: string; email: string; name: string; picture?: string; has_watch_history: boolean }

type AuthContextType = {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

const TOKEN_KEY = "lm_token"

function readToken(): string | null {
  try { return sessionStorage.getItem(TOKEN_KEY) ?? localStorage.getItem(TOKEN_KEY) } catch { return null }
}

function persistToken(t: string) {
  try { localStorage.setItem(TOKEN_KEY, t) } catch { /* storage unavailable */ }
  try { sessionStorage.setItem(TOKEN_KEY, t) } catch { /* storage unavailable */ }
}

function clearToken() {
  try { localStorage.removeItem(TOKEN_KEY) } catch { /* ignore */ }
  try { sessionStorage.removeItem(TOKEN_KEY) } catch { /* ignore */ }
}

function isTokenExpired(t: string): boolean {
  try {
    const payload = JSON.parse(atob(t.split(".")[1]))
    return typeof payload.exp === "number" && payload.exp * 1000 < Date.now()
  } catch { return false }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(() => {
    const t = readToken()
    if (t && isTokenExpired(t)) { clearToken(); return null }
    return t
  })
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    if (!token) return
    if (isTokenExpired(token)) { clearToken(); setToken(null); setUser(null); return }
    try {
      const me = await api.users.me(token)
      setUser({ id: me.id, email: me.email, name: me.name, picture: me.picture, has_watch_history: me.has_watch_history })
    } catch (err) {
      // Only invalidate the session on 401 Unauthorized.
      // Network errors or server downtime (502, 404, etc.) should not log the user out.
      if (err instanceof ApiError && err.status === 401) {
        clearToken()
        setToken(null)
        setUser(null)
      }
    }
  }, [token])

  useEffect(() => {
    if (token) {
      refreshUser().finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token, refreshUser])

  const saveSession = (accessToken: string, userData: User) => {
    persistToken(accessToken)
    setToken(accessToken)
    setUser(userData)
  }

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.auth.login(email, password)
    saveSession(res.access_token, res.user)
  }, [])

  const register = useCallback(async (email: string, password: string, name: string) => {
    const res = await api.auth.register(email, password, name)
    saveSession(res.access_token, res.user)
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
