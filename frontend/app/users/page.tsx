import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute"
import { UsersScreen } from "@/features/users/components/UsersScreen"

export default function UsersPage() {
  return (
    <ProtectedRoute allowedRoles={["jefe_operarios", "gerente"]}>
      <UsersScreen />
    </ProtectedRoute>
  )
}
