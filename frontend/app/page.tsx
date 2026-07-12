import GcoderWorkspace from "@/features/gcoder/components/layout/GcoderWorkspace"
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute"

export default function Page() {
  return (
    <ProtectedRoute>
      <GcoderWorkspace />
    </ProtectedRoute>
  )
}
