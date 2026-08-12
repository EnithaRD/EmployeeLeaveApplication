import {
    NavLink,
    Navigate,
    Route,
    Routes,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import Login from "../pages/auth/Login";
import Authenticated from "../pages/auth/Authenticated";
import ApplyLeave from "../pages/leave/ApplyLeave";
import Approvals from "../pages/leave/Approvals";
import Dashboard from "../pages/leave/Dashboard";
import MyLeaves from "../pages/leave/MyLeaves";
import ProtectedRoute from "./ProtectedRoute";


function AppShell({ children }) {

    const {
        user,
        logout,
    } = useAuth();

    const roleLabel = user?.role
        ? user.role.charAt(0) + user.role.slice(1).toLowerCase()
        : "Employee";
    const canApplyLeave = user?.role === "EMPLOYEE" || user?.role === "MANAGER";


    const navLinkClassName = ({ isActive }) =>
        `rounded-full px-4 py-2 transition ${
            isActive
                ? "bg-indigo-600 text-white shadow-sm"
                : "text-slate-700 hover:bg-slate-100"
        }`;


    return (
        <div className="min-h-screen bg-[radial-gradient(circle_at_top,#eef2ff,#f8fafc_40%,#f8fafc)] text-slate-900">

            <header className="sticky top-0 z-20 border-b border-white/70 bg-white/80 px-6 py-4 shadow-sm backdrop-blur">
                <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <div className="grid h-12 w-12 place-items-center rounded-2xl bg-indigo-600 text-lg font-bold text-white shadow-lg shadow-indigo-200">
                            EL
                        </div>
                        <div>
                            <div className="text-sm font-medium uppercase tracking-[0.2em] text-indigo-600">
                                Employee Leave App
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                                <p className="text-2xl font-semibold text-slate-900">
                                    Hello {roleLabel}
                                </p>
                                <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-700">
                                    {user?.role}
                                </span>
                            </div>
                        </div>
                    </div>

                    <nav className="flex flex-wrap items-center gap-2 text-sm text-slate-700">
                        <NavLink className={navLinkClassName} to="/" end>
                            Dashboard
                        </NavLink>
                        {canApplyLeave ? (
                            <NavLink className={navLinkClassName} to="/apply">
                                Apply Leave
                            </NavLink>
                        ) : null}
                        {canApplyLeave ? (
                            <NavLink className={navLinkClassName} to="/my-leaves">
                                My Leaves
                            </NavLink>
                        ) : null}
                        <NavLink className={navLinkClassName} to="/approvals">
                            Approvals
                        </NavLink>
                        <button
                            type="button"
                            onClick={logout}
                            className="rounded-full bg-slate-900 px-4 py-2 font-medium text-white shadow-sm transition hover:bg-slate-700"
                        >
                            Sign out
                        </button>
                    </nav>
                </div>
            </header>

            <main className="mx-auto max-w-7xl px-4 py-8">
                {children}
            </main>
        </div>
    );
}


function AppRoutes() {

    return (
        <Routes>

            <Route
                path="/"
                element={
                    <ProtectedRoute>
                        <AppShell>
                            <Dashboard />
                        </AppShell>
                    </ProtectedRoute>
                }
            />


            <Route
                path="/dashboard"
                element={
                    <ProtectedRoute>
                        <AppShell>
                            <Dashboard />
                        </AppShell>
                    </ProtectedRoute>
                }
            />

            <Route
                path="/login"
                element={<Login />}
            />


            <Route
                path="/apply"
                element={
                    <ProtectedRoute allowedRoles={["EMPLOYEE", "MANAGER"]}>
                        <AppShell>
                            <ApplyLeave />
                        </AppShell>
                    </ProtectedRoute>
                }
            />


            <Route
                path="/my-leaves"
                element={
                    <ProtectedRoute allowedRoles={["EMPLOYEE", "MANAGER"]}>
                        <AppShell>
                            <MyLeaves />
                        </AppShell>
                    </ProtectedRoute>
                }
            />


            <Route
                path="/approvals"
                element={
                    <ProtectedRoute>
                        <AppShell>
                            <Approvals />
                        </AppShell>
                    </ProtectedRoute>
                }
            />


            <Route
                path="/authenticated"
                element={
                    <ProtectedRoute>
                        <Authenticated />
                    </ProtectedRoute>
                }
            />


            <Route
                path="*"
                element={
                    <Navigate
                        to="/"
                        replace
                    />
                }
            />

        </Routes>
    );
}


export default AppRoutes;