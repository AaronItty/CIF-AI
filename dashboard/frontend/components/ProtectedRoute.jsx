import { Navigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  // While checking session
  if (loading) {
    return (
      <div style={{ padding: "2rem", textAlign: "center" }}>
        Loading...
      </div>
    )
  }

  // If not logged in
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // If logged in
  return children
}