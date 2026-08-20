import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'
import { type RunnerProfile } from '../api/client'

interface AuthContextType {
  user: RunnerProfile | null
  token: string | null
  login: (token: string, user: RunnerProfile) => void
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<RunnerProfile | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      axios.get('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => {
        setUser(res.data)
        if (res.data?.id) {
          localStorage.setItem('runner_id', String(res.data.id))
        }
      })
      .catch(() => {
        setToken(null)
        localStorage.removeItem('token')
        localStorage.removeItem('runner_id')
        localStorage.removeItem('runner_data')
      })
      .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token])

  const login = (newToken: string, newUser: RunnerProfile) => {
    localStorage.setItem('token', newToken)
    if (newUser?.id) {
      localStorage.setItem('runner_id', String(newUser.id))
    }
    setToken(newToken)
    setUser(newUser)
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('runner_id')
    localStorage.removeItem('runner_data')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
