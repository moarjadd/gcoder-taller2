"use client"

import { FormEvent, useEffect, useState } from "react"
import Link from "next/link"
import { ArrowLeft, KeyRound, LogOut, Plus, RotateCcw, Save, UserCog, UserRound, UserX } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/features/auth/context/AuthContext"
import {
  createUser,
  deactivateUser,
  fetchUsers,
  updateUser,
  type ManagedUser,
} from "@/features/users/api/usersClient"

function roleLabel(role: string | null) {
  if (role === "gerente") return "Gerente"
  if (role === "jefe_operarios") return "Jefe de operarios"
  if (role === "operario") return "Operario"
  return role ?? "-"
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

export function UsersScreen() {
  const { logout, role, token, username } = useAuth()
  const [users, setUsers] = useState<ManagedUser[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [newUsername, setNewUsername] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [editValues, setEditValues] = useState<Record<string, { username: string; password: string }>>({})

  const canManage = role === "jefe_operarios"

  async function loadUsers() {
    if (!token) return
    setIsLoading(true)
    setError(null)
    try {
      const result = await fetchUsers(token)
      setUsers(result)
      setEditValues(
        Object.fromEntries(result.map((user) => [user.id, { username: user.username, password: "" }])),
      )
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : "No se pudieron cargar los usuarios."
      setError(message)
      if (message.includes("sesion")) void logout(message)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadUsers()
  }, [token])

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token || !canManage) return
    setError(null)
    setSuccess(null)
    try {
      await createUser(token, { username: newUsername, password: newPassword, role: "operario" })
      setNewUsername("")
      setNewPassword("")
      setSuccess("Operario creado correctamente.")
      await loadUsers()
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "No se pudo crear el operario.")
    }
  }

  async function handleSave(user: ManagedUser) {
    if (!token || !canManage) return
    const values = editValues[user.id]
    if (!values) return
    const payload: { username?: string; password?: string } = {}
    if (values.username.trim() && values.username.trim() !== user.username) payload.username = values.username.trim()
    if (values.password.trim()) payload.password = values.password
    if (!payload.username && !payload.password) return

    setError(null)
    setSuccess(null)
    try {
      await updateUser(token, user.id, payload)
      setSuccess("Operario actualizado correctamente.")
      await loadUsers()
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "No se pudo actualizar el operario.")
    }
  }

  async function handleToggleActive(user: ManagedUser) {
    if (!token || !canManage) return
    setError(null)
    setSuccess(null)
    try {
      if (user.is_active) {
        await deactivateUser(token, user.id)
        setSuccess("Operario desactivado correctamente.")
      } else {
        await updateUser(token, user.id, { is_active: true })
        setSuccess("Operario reactivado correctamente.")
      }
      await loadUsers()
    } catch (toggleError) {
      setError(toggleError instanceof Error ? toggleError.message : "No se pudo cambiar el estado del operario.")
    }
  }

  function setEditValue(userId: string, field: "username" | "password", value: string) {
    setEditValues((current) => ({
      ...current,
      [userId]: {
        username: current[userId]?.username ?? "",
        password: current[userId]?.password ?? "",
        [field]: value,
      },
    }))
  }

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-[1500px] flex-col gap-5">
        <header className="flex flex-col gap-4 rounded-lg border border-border bg-card/80 p-4 backdrop-blur-sm lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <UserCog className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-2xl font-semibold text-foreground">Usuarios</h1>
              <p className="text-sm text-muted-foreground">
                {canManage ? "Gestion de usuarios operarios" : "Consulta de usuarios del sistema"}
              </p>
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

        {canManage && (
          <section className="rounded-lg border border-border bg-card/80 p-4 backdrop-blur-sm">
            <form className="grid gap-4 md:grid-cols-[1fr_1fr_auto]" onSubmit={handleCreate}>
              <div className="space-y-2">
                <Label htmlFor="new-username">Nuevo operario</Label>
                <Input
                  id="new-username"
                  value={newUsername}
                  onChange={(event) => setNewUsername(event.target.value)}
                  placeholder="operario2"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-password">Contraseña inicial</Label>
                <Input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  placeholder="Minimo 8 caracteres"
                  required
                />
              </div>
              <div className="flex items-end">
                <Button className="w-full md:w-auto" type="submit">
                  <Plus className="h-4 w-4" />
                  Crear operario
                </Button>
              </div>
            </form>
          </section>
        )}

        {(error || success) && (
          <div
            className={
              error
                ? "rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-red-200"
                : "rounded-md border border-primary/30 bg-primary/10 px-4 py-3 text-sm text-primary"
            }
          >
            {error ?? success}
          </div>
        )}

        <section className="rounded-lg border border-border bg-card/80 backdrop-blur-sm">
          <div className="border-b border-border px-4 py-3">
            <p className="text-sm text-muted-foreground">{users.length} usuarios visibles</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] text-left text-sm">
              <thead className="border-b border-border text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-4 py-3 font-medium">Usuario</th>
                  <th className="px-4 py-3 font-medium">Rol</th>
                  <th className="px-4 py-3 font-medium">Estado</th>
                  <th className="px-4 py-3 font-medium">Creado</th>
                  <th className="px-4 py-3 font-medium">Nueva contraseña</th>
                  <th className="px-4 py-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td className="px-4 py-8 text-center text-muted-foreground" colSpan={6}>
                      Cargando usuarios...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td className="px-4 py-8 text-center text-muted-foreground" colSpan={6}>
                      No hay usuarios para mostrar.
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr className="border-b border-border/60 last:border-0" key={user.id}>
                      <td className="px-4 py-3">
                        {canManage && user.role === "operario" ? (
                          <Input
                            value={editValues[user.id]?.username ?? user.username}
                            onChange={(event) => setEditValue(user.id, "username", event.target.value)}
                          />
                        ) : (
                          <span className="font-medium text-foreground">{user.username}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{roleLabel(user.role)}</td>
                      <td className="px-4 py-3">
                        <span className="rounded-full border border-border bg-background/50 px-2 py-1 text-xs text-foreground">
                          {user.is_active ? "Activo" : "Inactivo"}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">{formatDate(user.created_at)}</td>
                      <td className="px-4 py-3">
                        {canManage && user.role === "operario" ? (
                          <Input
                            type="password"
                            value={editValues[user.id]?.password ?? ""}
                            onChange={(event) => setEditValue(user.id, "password", event.target.value)}
                            placeholder="Dejar en blanco"
                          />
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {canManage && user.role === "operario" ? (
                          <div className="flex flex-wrap gap-2">
                            <Button type="button" variant="outline" size="sm" onClick={() => void handleSave(user)}>
                              {editValues[user.id]?.password ? <KeyRound className="h-4 w-4" /> : <Save className="h-4 w-4" />}
                              Guardar
                            </Button>
                            <Button type="button" variant="outline" size="sm" onClick={() => void handleToggleActive(user)}>
                              {user.is_active ? <UserX className="h-4 w-4" /> : <RotateCcw className="h-4 w-4" />}
                              {user.is_active ? "Desactivar" : "Reactivar"}
                            </Button>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">Solo lectura</span>
                        )}
                      </td>
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
