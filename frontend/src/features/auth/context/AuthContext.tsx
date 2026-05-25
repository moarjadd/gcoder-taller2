"use client"

import type React from "react"
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import {
  getCurrentUserRequest,
  loginRequest,
  logoutRequest,
  type AuthSession,
  type UserRole,
} from "@/features/auth/api/authClient"

type StoredAuthSession = {
  accessToken: string
  username: string
  role: UserRole
}

type AuthContextValue = {
  token: string | null
  username: string | null
  role: UserRole | null
  isAuthenticated: boolean
  isLoading: boolean
  authError: string | null
  login: (username: string, password: string) => Promise<void>
  logout: (message?: string) => Promise<void>
  clearAuthError: () => void
}

const STORAGE_KEY = "gcoder.auth"

const AuthContext = createContext<AuthContextValue | null>(null)

function readStoredSession(): StoredAuthSession | null {
  if (typeof window === "undefined") return null

  const rawSession = window.localStorage.getItem(STORAGE_KEY)
  if (!rawSession) return null

  try {
    const parsed = JSON.parse(rawSession) as Partial<StoredAuthSession>
    if (parsed.accessToken && parsed.username && parsed.role) {
      return {
        accessToken: parsed.accessToken,
        username: parsed.username,
        role: parsed.role,
      }
    }
  } catch {
    window.localStorage.removeItem(STORAGE_KEY)
  }

  return null
}

function persistSession(session: AuthSession) {
  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      accessToken: session.accessToken,
      username: session.username,
      role: session.role,
    }),
  )
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [authError, setAuthError] = useState<string | null>(null)

  const clearSession = useCallback((message?: string) => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(STORAGE_KEY)
    }
    setSession(null)
    setAuthError(message ?? null)
  }, [])

  const logout = useCallback(
    async (message?: string) => {
      const token = session?.accessToken
      if (token) {
        await logoutRequest(token)
      }
      clearSession(message)
    },
    [clearSession, session?.accessToken],
  )

  useEffect(() => {
    let isMounted = true

    async function restoreSession() {
      const storedSession = readStoredSession()
      if (!storedSession) {
        if (isMounted) setIsLoading(false)
        return
      }

      try {
        const currentUser = await getCurrentUserRequest(storedSession.accessToken)
        if (!isMounted) return
        const restoredSession = {
          accessToken: storedSession.accessToken,
          username: currentUser.username,
          role: currentUser.role,
        }
        setSession(restoredSession)
        persistSession(restoredSession)
      } catch (error) {
        if (!isMounted) return
        clearSession(error instanceof Error ? error.message : "Tu sesion expiro. Inicia sesion nuevamente.")
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    restoreSession()

    return () => {
      isMounted = false
    }
  }, [clearSession])

  const login = useCallback(async (username: string, password: string) => {
    const nextSession = await loginRequest(username, password)
    persistSession(nextSession)
    setSession(nextSession)
    setAuthError(null)
  }, [])

  const clearAuthError = useCallback(() => {
    setAuthError(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      token: session?.accessToken ?? null,
      username: session?.username ?? null,
      role: session?.role ?? null,
      isAuthenticated: Boolean(session?.accessToken),
      isLoading,
      authError,
      login,
      logout,
      clearAuthError,
    }),
    [authError, clearAuthError, isLoading, login, logout, session],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth debe usarse dentro de AuthProvider.")
  }
  return context
}
