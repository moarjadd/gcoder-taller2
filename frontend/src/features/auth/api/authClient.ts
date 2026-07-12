import { GCODER_API_BASE_URL } from "@/lib/env"

export type UserRole = "gerente" | "jefe_operarios" | "operario"

export type AuthSession = {
  accessToken: string
  username: string
  role: UserRole
}

export type CurrentUser = {
  id: string
  username: string
  role: UserRole
  is_active: boolean
  created_at: string
}

type LoginResponse = {
  access_token: string
  token_type: string
  username: string
  role: UserRole
}

async function readError(response: Response, fallback: string) {
  const body = await response.json().catch(() => null)
  return typeof body?.detail === "string" ? body.detail : fallback
}

export async function loginRequest(username: string, password: string): Promise<AuthSession> {
  let response: Response
  try {
    response = await fetch(`${GCODER_API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    })
  } catch {
    throw new Error("No se pudo conectar con el backend. Verifica que FastAPI este ejecutandose.")
  }

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Credenciales incorrectas.")
    }
    throw new Error(await readError(response, "No se pudo iniciar sesion."))
  }

  const payload = (await response.json()) as LoginResponse
  return {
    accessToken: payload.access_token,
    username: payload.username,
    role: payload.role,
  }
}

export async function getCurrentUserRequest(token: string): Promise<CurrentUser> {
  const response = await fetch(`${GCODER_API_BASE_URL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (response.status === 401) {
    throw new Error("Tu sesion expiro. Inicia sesion nuevamente.")
  }

  if (!response.ok) {
    throw new Error(await readError(response, "No se pudo validar la sesion."))
  }

  return response.json()
}

export async function logoutRequest(token: string): Promise<void> {
  await fetch(`${GCODER_API_BASE_URL}/api/auth/logout`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  }).catch(() => undefined)
}
