import { useEffect, useState } from "react"
import api from "../../services/api"
import { useAuth } from "../../context/AuthContext"

const statusStyles = {
  PENDING: "bg-amber-100 text-amber-800",
  APPROVED: "bg-emerald-100 text-emerald-800",
  REJECTED: "bg-red-100 text-red-800",
  CANCELLED: "bg-slate-100 text-slate-700",
}

export default function MyLeaves() {
  const { user } = useAuth()
  const [leaves, setLeaves] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadLeaves() {
      setLoading(true)
      try {
        const response = await api.get("/leaves/my")
        setLeaves(response.data)
      } catch (err) {
        setError("Unable to load leaves. Please refresh.")
      } finally {
        setLoading(false)
      }
    }

    loadLeaves()
  }, [])

  const cancelLeave = async (leaveId) => {
    try {
      await api.put(`/leaves/${leaveId}/cancel`)
      setLeaves((current) => current.map((leave) => {
        if (leave.id === leaveId) {
          return { ...leave, status: "CANCELLED" }
        }
        return leave
      }))
    } catch (error) {
      setError(error.response?.data?.detail || "Unable to cancel leave.")
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">My Leaves</h1>
          <p className="mt-2 text-sm text-slate-600">Review your leave history and cancel pending requests.</p>
        </div>
      </div>

      {error ? (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>
      ) : null}

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-4 font-medium text-slate-700">Leave type</th>
              <th className="px-6 py-4 font-medium text-slate-700">Dates</th>
              <th className="px-6 py-4 font-medium text-slate-700">Days</th>
              <th className="px-6 py-4 font-medium text-slate-700">Reason</th>
              <th className="px-6 py-4 font-medium text-slate-700">Status</th>
              <th className="px-6 py-4 font-medium text-slate-700">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading ? (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-slate-500">Loading leave history...</td>
              </tr>
            ) : leaves.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-slate-500">No leave requests found.</td>
              </tr>
            ) : (
              leaves.map((leave) => (
                <tr key={leave.id}>
                  <td className="whitespace-nowrap px-6 py-5 text-slate-800">{leave.leave_type_id}</td>
                  <td className="px-6 py-5 text-slate-600">{leave.start_date} → {leave.end_date}</td>
                  <td className="px-6 py-5 text-slate-600">{leave.days_count}</td>
                  <td className="px-6 py-5 text-slate-600">{leave.reason || "—"}</td>
                  <td className="px-6 py-5">
                    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${statusStyles[leave.status] || "bg-slate-100 text-slate-800"}`}>
                      {leave.status}
                    </span>
                  </td>
                  <td className="px-6 py-5">
                    {leave.status === "PENDING" ? (
                      <button
                        type="button"
                        onClick={() => cancelLeave(leave.id)}
                        className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-100"
                      >
                        Cancel
                      </button>
                    ) : (
                      <span className="text-sm text-slate-500">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
