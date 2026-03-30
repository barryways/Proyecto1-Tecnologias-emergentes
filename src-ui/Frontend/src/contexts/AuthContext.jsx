import { useState } from 'react'
import { clearStoredSession, loadStoredSession, saveStoredSession } from '../services/authStorage.js'
import { AuthContext } from './auth-context.js'

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => loadStoredSession())

  const persistSession = (authResponse) => {
    const nextSession = saveStoredSession(authResponse)
    setSession(nextSession)
    return nextSession
  }

  const logout = () => {
    clearStoredSession()
    setSession(null)
  }

  return (
    <AuthContext.Provider
      value={{
        session,
        user: session?.user ?? null,
        token: session?.accessToken ?? '',
        isAuthenticated: Boolean(session?.accessToken),
        persistSession,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
