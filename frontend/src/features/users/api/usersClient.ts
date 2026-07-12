import { GCODER_API_BASE_URL } from "@/lib/env"
import type { UserRole } from "@/features/auth/api/authClient"

export type ManagedUser = {
  id: string
  username: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export type CreateUserPayload = {
  username: string
  password: string
  role: "operario"
}

export type UpdateUserPayload = {
  username?: string
  password?: string
  is_active?: boolean
}

async function readError(response: Response, fallback: string) {
  const body = await response.json().catch(() => null)
  if (typeof body?.detail === "string") return body.detail
  if (Array.isArray(body?.detail)) {
    return body.detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join("; ") || fallback
  }
  return fallback
}

async function requestJson<T>(token: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${GCODER_API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  })

  if (response.status === 401) {
    throw new Error("Tu sesion expiro. Inicia sesion nuevamente.")
  }
  if (response.status === 403) {
    throw new Error("No tienes permisos para gestionar usuarios.")
  }
  if (!response.ok) {
    throw new Error(await readError(response, "No se pudo completar la operacion."))
  }
  return response.json()
}

export function fetchUsers(token: string): Promise<ManagedUser[]> {
  return requestJson<ManagedUser[]>(token, "/api/users")
}

export function createUser(token: string, payload: CreateUserPayload): Promise<ManagedUser> {
  return requestJson<ManagedUser>(token, "/api/users", {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function updateUser(token: string, userId: string, payload: UpdateUserPayload): Promise<ManagedUser> {
  return requestJson<ManagedUser>(token, `/api/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  })
}

export function deactivateUser(token: string, userId: string): Promise<ManagedUser> {
  return requestJson<ManagedUser>(token, `/api/users/${userId}`, {
    method: "DELETE",
  })
}
