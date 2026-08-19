import { useEffect, useState } from "react"
import api from "../../services/api"

const APPROVER_ROLES = ["MANAGER", "HR"]

export default function ApprovalFlowConfig() {
  const [flows, setFlows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [savingId, setSavingId] = useState(null)
  const [savedId, setSavedId] = useState(null)

  useEffect(() => {
    async function loadFlows() {
      setLoading(true)
      try {
        const response = await api.get("/approval-flows")
        setFlows(response.data)
      } catch (err) {
        setError("Unable to load approval flows. Please refresh.")
      } finally {
        setLoading(false)
      }
    }

    loadFlows()
  }, [])

  const updateStepRole = (leaveTypeId, stepIndex, role) => {
    setFlows((current) =>
      current.map((flow) =>
        flow.leave_type_id === leaveTypeId
          ? {
              ...flow,
              steps: flow.steps.map((step, index) =>
                index === stepIndex ? { ...step, approver_role: role } : step
              ),
            }
          : flow
      )
    )
  }

  const addStep = (leaveTypeId) => {
    setFlows((current) =>
      current.map((flow) =>
        flow.leave_type_id === leaveTypeId
          ? {
              ...flow,
              steps: [
                ...flow.steps,
                { step_order: flow.steps.length + 1, approver_role: "MANAGER" },
              ],
            }
          : flow
      )
    )
  }

  const removeStep = (leaveTypeId, stepIndex) => {
    setFlows((current) =>
      current.map((flow) =>
        flow.leave_type_id === leaveTypeId
          ? { ...flow, steps: flow.steps.filter((_, index) => index !== stepIndex) }
          : flow
      )
    )
  }

  const saveFlow = async (flow) => {
    setSavingId(flow.leave_type_id)
    setSavedId(null)
    setError(null)

    try {
      const response = await api.put(`/approval-flows/${flow.leave_type_id}`, {
        steps: flow.steps.map((step) => step.approver_role),
      })
      setFlows((current) =>
        current.map((existing) =>
          existing.leave_type_id === flow.leave_type_id ? response.data : existing
        )
      )
      setSavedId(flow.leave_type_id)
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to save approval flow.")
    } finally {
      setSavingId(null)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold text-slate-900">Approval Flow Configuration</h1>
        <p className="mt-2 text-sm text-slate-600">
          Choose which role(s) approve each leave type, and in what order. Changes apply to leave
          requests submitted after saving.
        </p>
      </div>

      {error ? (
        <div className="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>
      ) : null}

      {loading ? (
        <div className="text-sm text-slate-500">Loading approval flows...</div>
      ) : (
        <div className="space-y-6">
          {flows.map((flow) => (
            <div
              key={flow.leave_type_id}
              className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-xl font-semibold text-slate-900">{flow.leave_type_name}</h2>
                {savedId === flow.leave_type_id ? (
                  <span className="text-sm font-medium text-emerald-600">Saved</span>
                ) : null}
              </div>

              <div className="space-y-3">
                {flow.steps.length === 0 ? (
                  <p className="text-sm text-slate-500">No approval steps configured.</p>
                ) : (
                  flow.steps.map((step, index) => (
                    <div key={index} className="flex items-center gap-3">
                      <span className="w-16 text-sm font-medium text-slate-500">
                        Step {index + 1}
                      </span>
                      <select
                        value={step.approver_role}
                        onChange={(event) =>
                          updateStepRole(flow.leave_type_id, index, event.target.value)
                        }
                        className="block rounded-xl border border-slate-300 bg-white px-4 py-2 text-slate-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                      >
                        {APPROVER_ROLES.map((role) => (
                          <option key={role} value={role}>
                            {role}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => removeStep(flow.leave_type_id, index)}
                        className="rounded-xl border border-rose-200 bg-white px-3 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-50"
                      >
                        Remove
                      </button>
                    </div>
                  ))
                )}
              </div>

              <div className="mt-4 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => addStep(flow.leave_type_id)}
                  className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Add step
                </button>
                <button
                  type="button"
                  onClick={() => saveFlow(flow)}
                  disabled={savingId === flow.leave_type_id}
                  className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {savingId === flow.leave_type_id ? "Saving..." : "Save"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
