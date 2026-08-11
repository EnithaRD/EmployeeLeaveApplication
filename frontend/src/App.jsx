import { BrowserRouter, Routes, Route, Link, Navigate } from "react-router-dom"
import { AuthProvider, useAuth } from "./context/AuthContext"
import Dashboard from "./pages/leave/Dashboard"
import ApplyLeave from "./pages/leave/ApplyLeave"
import MyLeaves from "./pages/leave/MyLeaves"
import Approvals from "./pages/leave/Approvals"
import Login from "./pages/auth/Login"

function RequireAuth({ children }) {
  const { user } = useAuth()
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return children
}

function AppRoutes() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4">
          <div className="text-lg font-semibold">Employee Leave App</div>
          <nav className="flex flex-wrap items-center gap-2 text-sm text-slate-700">
            <Link className="rounded-xl px-3 py-2 hover:bg-slate-100" to="/">Dashboard</Link>
            <Link className="rounded-xl px-3 py-2 hover:bg-slate-100" to="/apply">Apply Leave</Link>
            <Link className="rounded-xl px-3 py-2 hover:bg-slate-100" to="/my-leaves">My Leaves</Link>
            <Link className="rounded-xl px-3 py-2 hover:bg-slate-100" to="/approvals">Approvals</Link>
            {user ? (
              <button
                type="button"
                onClick={logout}
                className="rounded-xl border border-slate-200 bg-slate-100 px-3 py-2 hover:bg-slate-200"
              >
                Sign out
              </button>
            ) : (
              <Link className="rounded-xl px-3 py-2 hover:bg-slate-100" to="/login">Sign In</Link>
            )}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
          <Route path="/apply" element={<RequireAuth><ApplyLeave /></RequireAuth>} />
          <Route path="/my-leaves" element={<RequireAuth><MyLeaves /></RequireAuth>} />
          <Route path="/approvals" element={<RequireAuth><Approvals /></RequireAuth>} />
        </Routes>
      </main>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
