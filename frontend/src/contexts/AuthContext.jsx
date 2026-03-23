import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { login as apiLogin, signup as apiSignup } from '../api/auth'
import client from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('user')
    return stored ? JSON.parse(stored) : null
  })

  // If an access token exists but no user object (e.g., page reload), try fetching /users/me
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token && !user) {
      let mounted = true
      client
        .get('/users/me')
        .then((res) => {
          if (mounted && res.data) {
            localStorage.setItem('user', JSON.stringify(res.data))
            setUser(res.data)
          }
        })
        .catch(() => {
          // if token invalid, clear stored auth
          localStorage.removeItem('access_token')
          localStorage.removeItem('user')
          setUser(null)
        })
      return () => { mounted = false }
    }
  }, [user])

  const login = useCallback(async (credentials) => {
    const { data } = await apiLogin(credentials)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    setUser(data.user)
    return data.user
  }, [])

  const signup = useCallback(async (credentials) => {
    const { data } = await apiSignup(credentials)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    setUser(data.user)
    return data.user
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    setUser(null)
  }, [])

  const refreshUser = useCallback((updatedUser) => {
    setUser(updatedUser)
    localStorage.setItem('user', JSON.stringify(updatedUser))
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
