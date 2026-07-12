import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute"
import { LogsScreen } from "@/features/logs/components/LogsScreen"

export default function LogsPage() {
  return (
    <ProtectedRoute allowedRoles={["gerente"]}>
      <LogsScreen />
    </ProtectedRoute>
  )
}
