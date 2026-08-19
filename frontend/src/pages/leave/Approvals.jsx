import { useEffect, useState } from "react"
import api from "../../services/api"
import { useAuth } from "../../context/AuthContext"

export default function Approvals() {
  const { user } = useAuth()
  const [pendingLeaves, setPendingLeaves] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeRejectId, setActiveRejectId] = useState(null)
  const [comment, setComment] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [leaveTypesById, setLeaveTypesById] = useState({})
  const [documentError, setDocumentError] = useState(null)

  useEffect(() => {
    async function loadPending() {
      setLoading(true)
      try {
        const response = await api.get("/leaves/pending")
        setPendingLeaves(response.data)
      } catch (err) {
        setError("Unable to load pending approvals. Please refresh.")
      } finally {
        setLoading(false)
      }
    }

    async function loadLeaveTypes() {
      try {
        const response = await api.get("/leave-types")
        setLeaveTypesById(
          Object.fromEntries(response.data.map((type) => [type.id, type.name]))
        )
      } catch (err) {
        // Leave type names are a display nicety; failing to load them shouldn't block approvals.
      }
    }

    loadPending()
    loadLeaveTypes()
  }, [])

  const viewDocument = async (leaveId) => {
    setDocumentError(null)
    try {
      const response = await api.get(`/leaves/${leaveId}/document`, { responseType: "blob" })
      const url = URL.createObjectURL(response.data)
      window.open(url, "_blank", "noopener,noreferrer")
    } catch (err) {
      setDocumentError(err.response?.data?.detail || "Unable to load the document.")
    }
  }

  const updateLeaveStatus = async (leaveId, action, reviewComment) => {
    setIsSubmitting(true)
    setError(null)

    try {
      await api.put(`/leaves/${leaveId}/decide`, {
        action,
        comment: reviewComment,
      })
      setPendingLeaves((current) => current.filter((leave) => leave.id !== leaveId))
      setActiveRejectId(null)
      setComment("")
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to submit decision.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-6 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">Pending Approvals</h1>
          <p className="mt-2 text-sm text-slate-600">Review pending leave requests from your team.</p>
        </div>
        <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <p className="font-medium">Role</p>
          <p>{user?.role || "Manager"}</p>
        </div>
      </div>

      {error ? (
        <div className="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>
      ) : null}

      {documentError ? (
        <div className="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{documentError}</div>
      ) : null}

      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-4 font-medium text-slate-700">Employee</th>
              <th className="px-6 py-4 font-medium text-slate-700">Leave type</th>
              <th className="px-6 py-4 font-medium text-slate-700">Dates</th>
              <th className="px-6 py-4 font-medium text-slate-700">Days</th>
              <th className="px-6 py-4 font-medium text-slate-700">Reason</th>
              <th className="px-6 py-4 font-medium text-slate-700">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {loading ? (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-slate-500">Loading pending requests...</td>
              </tr>
            ) : pendingLeaves.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-slate-500">No pending leave requests.</td>
              </tr>
            ) : (
              pendingLeaves.map((leave) => (
                <tr key={leave.id}>
                  <td className="whitespace-nowrap px-6 py-5 text-slate-800">{leave.employee_id}</td>
                  <td className="px-6 py-5 text-slate-600">{leaveTypesById[leave.leave_type_id] || leave.leave_type_id}</td>
                  <td className="px-6 py-5 text-slate-600">{leave.start_date} → {leave.end_date}</td>
                  <td className="px-6 py-5 text-slate-600">{leave.days_count}</td>
                  <td className="px-6 py-5 text-slate-600">{leave.reason || "No reason provided"}</td>
                  <td className="px-6 py-5 space-y-3">
                    {leaveTypesById[leave.leave_type_id] === "Sick Leave" ? (
                      <button
                        type="button"
                        onClick={() => viewDocument(leave.id)}
                        className="inline-flex w-full items-center justify-center rounded-xl border border-indigo-200 bg-white px-3 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-50"
                      >
                        View document
                      </button>
                    ) : null}
                    <button
                      type="button"
                      onClick={() => updateLeaveStatus(leave.id, "APPROVED", "")}
                      disabled={isSubmitting}
                      className="inline-flex w-full items-center justify-center rounded-xl bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveRejectId(activeRejectId === leave.id ? null : leave.id)}
                      className="inline-flex w-full items-center justify-center rounded-xl border border-rose-200 bg-white px-3 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-50"
                    >
                      Reject
                    </button>
                    {activeRejectId === leave.id ? (
                      <div className="mt-3 space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-3">
                        <textarea
                          rows={3}
                          value={comment}
                          onChange={(event) => setComment(event.target.value)}
                          className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-slate-900 shadow-sm focus:border-rose-500 focus:outline-none focus:ring-2 focus:ring-rose-100"
                          placeholder="Add a rejection comment (optional)"
                        />
                        <button
                          type="button"
                          onClick={() => updateLeaveStatus(leave.id, "REJECTED", comment)}
                          disabled={isSubmitting}
                          className="inline-flex w-full items-center justify-center rounded-xl bg-rose-600 px-3 py-2 text-sm font-semibold text-white hover:bg-rose-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                        >
                          Submit rejection
                        </button>
                      </div>
                    ) : null}
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
