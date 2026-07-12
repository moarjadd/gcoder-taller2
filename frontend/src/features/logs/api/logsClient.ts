import { GCODER_API_BASE_URL } from "@/lib/env"

export type AuditLog = {
  id: string
  user_id: string | null
  username_snapshot: string | null
  user_role: string | null
  action: string
  resource: string | null
  file_name: string | null
  file_extension: string | null
  status: string
  detail: string | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export type AuditLogFilters = {
  username?: string
  action?: string
  status?: string
  file_extension?: string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}

export type AuditLogList = {
  total: number
  limit: number
  offset: number
  items: AuditLog[]
}

export async function fetchAuditLogs(token: string, filters: AuditLogFilters = {}): Promise<AuditLogList> {
  const searchParams = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      searchParams.set(key, String(value))
    }
  })

  const query = searchParams.toString()
  const response = await fetch(`${GCODER_API_BASE_URL}/api/logs${query ? `?${query}` : ""}`, {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (response.status === 401) {
    throw new Error("Tu sesion expiro. Inicia sesion nuevamente.")
  }

  if (response.status === 403) {
    throw new Error("No tienes permisos para ver los logs globales.")
  }

  if (!response.ok) {
    throw new Error("No se pudieron cargar los logs.")
  }

  return response.json()
}
