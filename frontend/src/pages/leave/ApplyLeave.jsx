import { useEffect, useState } from "react"
import api from "../../services/api"
import { useAuth } from "../../context/AuthContext"

const statusClasses = {
  success: "text-green-700 bg-green-100 border-green-200",
  error: "text-red-700 bg-red-100 border-red-200",
}

export default function ApplyLeave() {
  const { user } = useAuth()
  const [leaveTypes, setLeaveTypes] = useState([])
  const [selectedType, setSelectedType] = useState("")
  const [startDate, setStartDate] = useState("")
  const [endDate, setEndDate] = useState("")
  const [reason, setReason] = useState("")
  const [availableBalance, setAvailableBalance] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [feedback, setFeedback] = useState(null)
  const [document, setDocument] = useState(null)

  const selectedLeaveTypeName = leaveTypes.find((type) => String(type.id) === String(selectedType))?.name
  const isSickLeave = selectedLeaveTypeName === "Sick Leave"

  useEffect(() => {
    async function loadLeaveTypes() {
      try {
        const response = await api.get("/leave-types")
        setLeaveTypes(response.data)
      } catch (error) {
        setFeedback({
          type: "error",
          message: "Unable to load leave types. Please refresh.",
        })
      }
    }

    loadLeaveTypes()
  }, [])

  useEffect(() => {
    async function loadAvailable() {
      if (!selectedType) {
        setAvailableBalance(null)
        return
      }

      try {
        const response = await api.get("/leaves/available", {
          params: { leave_type_id: selectedType },
        })
        setAvailableBalance(response.data.available)
      } catch (error) {
        setAvailableBalance(null)
      }
    }

    loadAvailable()
  }, [selectedType])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setIsSubmitting(true)
    setFeedback(null)

    try {
      const response = await api.post("/leaves/apply", {
        leave_type_id: Number(selectedType),
        start_date: startDate,
        end_date: endDate,
        reason,
      })

      if (isSickLeave && document) {
        const formData = new FormData()
        formData.append("file", document)
        await api.post(`/leaves/${response.data.id}/document`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        })
      }

      setFeedback({
        type: "success",
        message: "Leave request submitted successfully.",
      })
      setReason("")
      setStartDate("")
      setEndDate("")
      setSelectedType("")
      setAvailableBalance(null)
      setDocument(null)
    } catch (error) {
      const message = error.response?.data?.detail || "Unable to submit leave request."
      setFeedback({ type: "error", message })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold text-slate-900">Apply for Leave</h1>
        <p className="mt-2 text-sm text-slate-600">Submit a leave request and review your available balance before applying.</p>
      </div>

      {feedback ? (
        <div className={`mb-6 rounded-lg border px-4 py-3 ${statusClasses[feedback.type] || "bg-slate-100 text-slate-900 border-slate-200"}`}>
          {feedback.message}
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="space-y-6 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div>
          <label htmlFor="leaveType" className="block text-sm font-medium text-slate-700">Leave type</label>
          <select
            id="leaveType"
            value={selectedType}
            onChange={(event) => setSelectedType(event.target.value)}
            className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
          >
            <option value="">Select leave type</option>
            {leaveTypes.map((type) => (
              <option key={type.id} value={type.id}>
                {type.name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <label htmlFor="startDate" className="block text-sm font-medium text-slate-700">Start date</label>
            <input
              id="startDate"
              type="date"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
              className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
          </div>
          <div>
            <label htmlFor="endDate" className="block text-sm font-medium text-slate-700">End date</label>
            <input
              id="endDate"
              type="date"
              value={endDate}
              onChange={(event) => setEndDate(event.target.value)}
              className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
          </div>
        </div>

        <div>
          <label htmlFor="reason" className="block text-sm font-medium text-slate-700">Reason</label>
          <textarea
            id="reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            rows={4}
            className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            placeholder="Enter a short explanation for your leave request"
          />
        </div>

        {isSickLeave ? (
          <div>
            <label htmlFor="document" className="block text-sm font-medium text-slate-700">
              Supporting document (optional)
            </label>
            <input
              id="document"
              type="file"
              onChange={(event) => setDocument(event.target.files?.[0] || null)}
              className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
          </div>
        ) : null}

        <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
          <p className="font-medium">Available balance</p>
          <p className="mt-1 text-xl font-semibold text-slate-900">
            {selectedType ? (
              availableBalance === null ? "Loading..." : `${availableBalance} days available`
            ) : (
              "Select a leave type to view available balance"
            )}
          </p>
        </div>

        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm text-slate-500">Logged in as {user?.full_name || user?.email || "Employee"}</p>
          </div>
          <button
            type="submit"
            disabled={isSubmitting || !selectedType || !startDate || !endDate}
            className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isSubmitting ? "Submitting..." : "Submit request"}
          </button>
        </div>
      </form>
    </div>
  )
}
