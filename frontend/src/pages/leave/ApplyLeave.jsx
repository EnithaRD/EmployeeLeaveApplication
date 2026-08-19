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
  const [certificateFile, setCertificateFile] = useState(null)
  const [certificateError, setCertificateError] = useState(null)
  const [availableBalance, setAvailableBalance] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [feedback, setFeedback] = useState(null)

  const ALLOWED_CERTIFICATE_TYPES = ["application/pdf", "image/jpeg", "image/png"]
  const MAX_CERTIFICATE_SIZE_BYTES = 5 * 1024 * 1024

  const selectedLeaveTypeName = leaveTypes.find((type) => String(type.id) === String(selectedType))?.name || ""
  const isSickLeave = selectedLeaveTypeName.trim().toLowerCase() === "sick leave"

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

  useEffect(() => {
    setCertificateFile(null)
    setCertificateError(null)
  }, [selectedType])

  const handleCertificateChange = (event) => {
    const file = event.target.files?.[0] || null

    if (!file) {
      setCertificateFile(null)
      setCertificateError(null)
      return
    }

    if (!ALLOWED_CERTIFICATE_TYPES.includes(file.type)) {
      setCertificateFile(null)
      setCertificateError("Unsupported file type. Please upload a PDF, JPG, or PNG file.")
      event.target.value = ""
      return
    }

    if (file.size > MAX_CERTIFICATE_SIZE_BYTES) {
      setCertificateFile(null)
      setCertificateError("File is too large. Maximum allowed size is 5MB.")
      event.target.value = ""
      return
    }

    setCertificateFile(file)
    setCertificateError(null)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (isSickLeave && !certificateFile) {
      setCertificateError("A medical certificate is required for Sick Leave.")
      return
    }

    setIsSubmitting(true)
    setFeedback(null)

    try {
      const formData = new FormData()
      formData.append("leave_type_id", Number(selectedType))
      formData.append("start_date", startDate)
      formData.append("end_date", endDate)
      formData.append("reason", reason)
      if (certificateFile) {
        formData.append("medical_certificate", certificateFile)
      }

      await api.post("/leaves/apply", formData, {
        headers: { "Content-Type": undefined },
      })

      setFeedback({
        type: "success",
        message: "Leave request submitted successfully.",
      })
      setReason("")
      setStartDate("")
      setEndDate("")
      setSelectedType("")
      setAvailableBalance(null)
      setCertificateFile(null)
      setCertificateError(null)
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

        {isSickLeave ? (
          <div>
            <label htmlFor="medicalCertificate" className="block text-sm font-medium text-slate-700">
              Medical certificate <span className="text-red-600">(required)</span>
            </label>
            <input
              id="medicalCertificate"
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
              onChange={handleCertificateChange}
              className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
            <p className="mt-1 text-xs text-slate-500">PDF, JPG, or PNG. Maximum size 5MB.</p>
            {certificateFile ? (
              <p className="mt-1 text-xs text-slate-600">Selected file: {certificateFile.name}</p>
            ) : null}
            {certificateError ? (
              <p className="mt-1 text-xs text-red-600">{certificateError}</p>
            ) : null}
          </div>
        ) : null}

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
            disabled={isSubmitting || !selectedType || !startDate || !endDate || (isSickLeave && !certificateFile)}
            className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isSubmitting ? "Submitting..." : "Submit request"}
          </button>
        </div>
      </form>
    </div>
  )
}
