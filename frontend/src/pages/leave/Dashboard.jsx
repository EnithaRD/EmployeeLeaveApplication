import { useEffect, useState } from "react"
import api from "../../services/api"
import { useAuth } from "../../context/AuthContext"
import MonthlyLeaveStackedChart from "../../components/MonthlyLeaveStackedChart"

const SUMMARY_YEAR = 2026

async function fetchAdminDashboardData() {
  const [summaryResponse, pendingResponse] = await Promise.all([
    api.get(`/leaves/monthly-summary?year=${SUMMARY_YEAR}`),
    api.get("/leaves/pending-count"),
  ])
  return {
    monthlySummary: summaryResponse.data,
    pendingCount: pendingResponse.data.count,
  }
}

async function fetchEmployeeDashboardData() {
  const [balanceResponse, pendingResponse] = await Promise.all([
    api.get("/leaves/balances"),
    api.get("/leaves/pending-count"),
  ])
  return {
    balances: balanceResponse.data,
    pendingCount: pendingResponse.data.count,
  }
}

export default function Dashboard() {
  const { user } = useAuth()
  const isAdmin = user?.role === "ADMIN"
  const [balances, setBalances] = useState([])
  const [monthlySummary, setMonthlySummary] = useState([])
  const [pendingCount, setPendingCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!user) {
      return
    }

    async function loadData() {
      setLoading(true)
      try {
        if (isAdmin) {
          const data = await fetchAdminDashboardData()
          setMonthlySummary(data.monthlySummary)
          setPendingCount(data.pendingCount)
        } else {
          const data = await fetchEmployeeDashboardData()
          setBalances(data.balances)
          setPendingCount(data.pendingCount)
        }
      } catch (err) {
        setError("Unable to load dashboard data. Please refresh.")
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [user, isAdmin])

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
          <p className="mt-2 text-m text-slate-600">Quick view of your leave balances and pending approvals.</p>
        </div>
      </div>

      {error ? (
        <div className="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-2">
        {isAdmin ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Leave Requests by Month ({SUMMARY_YEAR})</h2>
                <p className="mt-1 text-sm text-slate-500">Approved vs rejected leave requests, by month.</p>
              </div>
            </div>
            {loading ? (
              <div className="text-sm text-slate-500">Loading chart data...</div>
            ) : (
              <MonthlyLeaveStackedChart data={monthlySummary} />
            )}
          </div>
        ) : (
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Leave Balances</h2>
                <p className="mt-1 text-sm text-slate-500">Your current balances by leave type.</p>
              </div>
            </div>
            <div className="space-y-4">
              {loading ? (
                <div className="text-sm text-slate-500">Loading balances...</div>
              ) : balances.length === 0 ? (
                <div className="text-sm text-slate-500">No leave balances available.</div>
              ) : (
                balances.map((balance) => (
                  <div key={balance.id} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-slate-700">{balance.leave_type_name}</p>
                        <p className="text-sm text-slate-500">Year {balance.year}</p>
                      </div>
                      <div className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white">
                        {balance.allocated - balance.used} days
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-3 text-sm text-slate-600">
                      <div>Allocated: {balance.allocated}</div>
                      <div>Used: {balance.used}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {user?.role === "MANAGER" || user?.role === "ADMIN" ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-5">
              <h2 className="text-xl font-semibold text-slate-900">Pending Approvals</h2>
              <p className="mt-1 text-sm text-slate-500">Team requests that need your review.</p>
            </div>
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6 text-center">
              <p className="text-5xl font-semibold text-slate-900">{loading ? "..." : pendingCount}</p>
              <p className="mt-2 text-sm text-slate-600">Pending leave requests</p>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
