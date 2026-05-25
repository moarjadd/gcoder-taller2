"use client"

import type React from "react"
import { useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { ShieldAlert, Settings } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { UserRole } from "@/features/auth/api/authClient"
import { useAuth } from "@/features/auth/context/AuthContext"

export function ProtectedRoute({
  allowedRoles,
  children,
}: {
  allowedRoles?: UserRole[]
  children: React.ReactNode
}) {
  const { isAuthenticated, isLoading, role } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login")
    }
  }, [isAuthenticated, isLoading, router])

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="flex items-center gap-3 rounded-lg border border-border bg-card/80 px-5 py-4 text-muted-foreground shadow-sm backdrop-blur-sm">
          <Settings className="h-5 w-5 animate-spin text-primary" />
          <span className="text-sm">Validando sesion...</span>
        </div>
      </div>
    )
  }

  if (allowedRoles && (!role || !allowedRoles.includes(role))) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-md rounded-lg border border-border bg-card/90 p-6 text-center shadow-sm backdrop-blur-sm">
          <ShieldAlert className="mx-auto mb-4 h-10 w-10 text-destructive" />
          <h1 className="text-xl font-semibold text-foreground">Acceso denegado</h1>
          <p className="mt-2 text-sm text-muted-foreground">Tu rol no tiene permisos para ver esta pantalla.</p>
          <Button asChild className="mt-5">
            <Link href="/">Volver al conversor</Link>
          </Button>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
