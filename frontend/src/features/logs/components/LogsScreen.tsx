"use client"

import { FormEvent, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { ArrowLeft, LogOut, Search, ShieldCheck, UserRound } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/features/auth/context/AuthContext"
import { fetchAuditLogs, type AuditLog, type AuditLogFilters } from "@/features/logs/api/logsClient"

function roleLabel(role: string | null) {
  if (role === "gerente") return "Gerente"
  if (role === "jefe_operarios") return "Jefe de operarios"
  if (role === "operario") return "Operario"
  return role ?? "-"
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(new Date(value))
}

function fileLabel(log: AuditLog) {
  return log.file_name ?? "-"
}

export function LogsScreen() {
  const { logout, role, token, username } = useAuth()
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<AuditLogFilters>({ limit: 50, offset: 0 })
  const [draftFilters, setDraftFilters] = useState<AuditLogFilters>({ limit: 50, offset: 0 })

  const canViewLogs = role === "gerente"

  useEffect(() => {
    let isMounted = true

    async function loadLogs() {
      if (!token || !canViewLogs) return
      setIsLoading(true)
      setError(null)
      try {
        const result = await fetchAuditLogs(token, filters)
        if (!isMounted) return
        setLogs(result.items)
        setTotal(result.total)
      } catch (loadError) {
        if (!isMounted) return
        setError(loadError instanceof Error ? loadError.message : "No se pudieron cargar los logs.")
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    loadLogs()

    return () => {
      isMounted = false
    }
  }, [canViewLogs, filters, token])

  const statusSummary = useMemo(() => {
    const counts = logs.reduce<Record<string, number>>((acc, log) => {
      acc[log.status] = (acc[log.status] ?? 0) + 1
      return acc
    }, {})
    return Object.entries(counts)
      .map(([status, count]) => `${status}: ${count}`)
      .join(" · ")
  }, [logs])

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFilters({ ...draftFilters, limit: 50, offset: 0 })
  }

  function updateDraftFilter(key: keyof AuditLogFilters, value: string) {
    setDraftFilters((current) => ({
      ...current,
      [key]: value,
    }))
  }

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-[1800px] flex-col gap-5">
        <header className="flex flex-col gap-4 rounded-lg border border-border bg-card/80 p-4 backdrop-blur-sm lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <ShieldCheck className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-semibold text-foreground">Auditoria</h1>
                <p className="text-sm text-muted-foreground">Bitacora de actividad de usuarios y conversiones</p>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 rounded-md border border-border bg-background/40 px-3 py-2 text-sm">
              <UserRound className="h-4 w-4 text-primary" />
              <span className="font-medium text-foreground">{username}</span>
              <span className="text-muted-foreground">{roleLabel(role)}</span>
            </div>
            <Button asChild variant="outline" size="sm">
              <Link href="/">
                <ArrowLeft className="h-4 w-4" />
                Conversor
              </Link>
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => void logout()}>
              <LogOut className="h-4 w-4" />
              Cerrar sesion
            </Button>
          </div>
        </header>

        <section className="rounded-lg border border-border bg-card/80 p-4 backdrop-blur-sm">
          <form className="grid gap-4 md:grid-cols-2 xl:grid-cols-6" onSubmit={handleSubmit}>
            <div className="space-y-2">
              <Label htmlFor="username">Usuario</Label>
              <Input id="username" value={draftFilters.username ?? ""} onChange={(event) => updateDraftFilter("username", event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="action">Accion</Label>
              <Input id="action" value={draftFilters.action ?? ""} onChange={(event) => updateDraftFilter("action", event.target.value)} placeholder="LOGIN_SUCCESS" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="status">Estado</Label>
              <Input id="status" value={draftFilters.status ?? ""} onChange={(event) => updateDraftFilter("status", event.target.value)} placeholder="success" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="file_extension">Extension</Label>
              <Input id="file_extension" value={draftFilters.file_extension ?? ""} onChange={(event) => updateDraftFilter("file_extension", event.target.value)} placeholder="stl" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="date_from">Desde</Label>
              <Input id="date_from" type="date" value={draftFilters.date_from ?? ""} onChange={(event) => updateDraftFilter("date_from", event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="date_to">Hasta</Label>
              <div className="flex gap-2">
                <Input id="date_to" type="date" value={draftFilters.date_to ?? ""} onChange={(event) => updateDraftFilter("date_to", event.target.value)} />
                <Button type="submit" size="icon" aria-label="Filtrar logs">
                  <Search className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </form>
        </section>

        <section className="rounded-lg border border-border bg-card/80 backdrop-blur-sm">
          <div className="flex flex-col gap-2 border-b border-border px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              {total} registros encontrados{statusSummary ? ` · ${statusSummary}` : ""}
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[1100px] text-left text-sm">
              <thead className="border-b border-border text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Fecha</th>
                  <th className="px-4 py-3 font-medium">Usuario</th>
                  <th className="px-4 py-3 font-medium">Rol</th>
                  <th className="px-4 py-3 font-medium">Accion</th>
                  <th className="px-4 py-3 font-medium">Estado</th>
                  <th className="px-4 py-3 font-medium">Archivo</th>
                  <th className="px-4 py-3 font-medium">Ext.</th>
                  <th className="px-4 py-3 font-medium">Detalle</th>
                  <th className="px-4 py-3 font-medium">IP</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td className="px-4 py-8 text-center text-muted-foreground" colSpan={9}>
                      Cargando logs...
                    </td>
                  </tr>
                ) : error ? (
                  <tr>
                    <td className="px-4 py-8 text-center text-destructive" colSpan={9}>
                      {error}
                    </td>
                  </tr>
                ) : logs.length === 0 ? (
                  <tr>
                    <td className="px-4 py-8 text-center text-muted-foreground" colSpan={9}>
                      No hay registros para los filtros seleccionados.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr className="border-b border-border/60 last:border-0" key={log.id}>
                      <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">{formatDate(log.created_at)}</td>
                      <td className="px-4 py-3 text-foreground">{log.username_snapshot ?? log.user_id ?? "-"}</td>
                      <td className="px-4 py-3 text-muted-foreground">{roleLabel(log.user_role)}</td>
                      <td className="px-4 py-3 font-medium text-foreground">{log.action}</td>
                      <td className="px-4 py-3">
                        <span className="rounded-full border border-border bg-background/50 px-2 py-1 text-xs text-foreground">
                          {log.status}
                        </span>
                      </td>
                      <td className="max-w-[220px] truncate px-4 py-3 text-muted-foreground">{fileLabel(log)}</td>
                      <td className="px-4 py-3 text-muted-foreground">{log.file_extension ?? "-"}</td>
                      <td className="max-w-[340px] truncate px-4 py-3 text-muted-foreground" title={log.detail ?? ""}>
                        {log.detail ?? "-"}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{log.ip_address ?? "-"}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  )
}
