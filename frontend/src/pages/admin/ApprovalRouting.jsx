import { useEffect, useState } from "react"
import api from "../../services/api"

const AVAILABLE_ROLES = ["MANAGER", "HR", "ADMIN"]

export default function ApprovalRouting() {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [savingLeaveTypeId, setSavingLeaveTypeId] = useState(null)

  const loadRules = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.get("/admin/approval-routing")
      setRules(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to load approval routing configuration.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadRules()
  }, [])

  const toggleRole = (leaveTypeId, role) => {
    setRules((current) =>
      current.map((rule) => {
        if (rule.leave_type_id !== leaveTypeId) {
          return rule
        }
        const hasRole = rule.approval_chain.includes(role)
        const approval_chain = hasRole
          ? rule.approval_chain.filter((existing) => existing !== role)
          : [...rule.approval_chain, role]
        return { ...rule, approval_chain }
      })
    )
  }

  const moveRole = (leaveTypeId, index, direction) => {
    setRules((current) =>
      current.map((rule) => {
        if (rule.leave_type_id !== leaveTypeId) {
          return rule
        }
        const chain = [...rule.approval_chain]
        const targetIndex = index + direction
        if (targetIndex < 0 || targetIndex >= chain.length) {
          return rule
        }
        ;[chain[index], chain[targetIndex]] = [chain[targetIndex], chain[index]]
        return { ...rule, approval_chain: chain }
      })
    )
  }

  const saveRule = async (rule) => {
    setSavingLeaveTypeId(rule.leave_type_id)
    setError(null)
    try {
      const response = await api.put(`/admin/approval-routing/${rule.leave_type_id}`, {
        approval_chain: rule.approval_chain,
      })
      setRules((current) =>
        current.map((existing) =>
          existing.leave_type_id === rule.leave_type_id ? response.data : existing
        )
      )
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to save approval routing.")
    } finally {
      setSavingLeaveTypeId(null)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold text-slate-900">Approval Routing</h1>
        <p className="mt-2 text-sm text-slate-600">
          Configure which roles must approve each leave type, in order. Changes apply to newly submitted requests.
        </p>
      </div>

      {error ? (
        <div className="mb-6 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">{error}</div>
      ) : null}

      {loading ? (
        <div className="text-sm text-slate-500">Loading...</div>
      ) : (
        <div className="space-y-4">
          {rules.map((rule) => (
            <div key={rule.leave_type_id} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-slate-900">{rule.leave_type_name}</h2>
                <button
                  type="button"
                  onClick={() => saveRule(rule)}
                  disabled={savingLeaveTypeId === rule.leave_type_id || rule.approval_chain.length === 0}
                  className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {savingLeaveTypeId === rule.leave_type_id ? "Saving..." : "Save"}
                </button>
              </div>

              <div className="mb-4 flex flex-wrap gap-2">
                {AVAILABLE_ROLES.map((role) => (
                  <label
                    key={role}
                    className="flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-sm text-slate-700"
                  >
                    <input
                      type="checkbox"
                      checked={rule.approval_chain.includes(role)}
                      onChange={() => toggleRole(rule.leave_type_id, role)}
                    />
                    {role}
                  </label>
                ))}
              </div>

              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">Approval order</p>
                {rule.approval_chain.length === 0 ? (
                  <p className="text-sm text-rose-600">Select at least one approver role.</p>
                ) : (
                  <ol className="flex flex-wrap items-center gap-2">
                    {rule.approval_chain.map((role, index) => (
                      <li key={role} className="flex items-center gap-1 rounded-xl bg-slate-100 px-3 py-2 text-sm">
                        <span className="font-semibold text-slate-800">
                          {index + 1}. {role}
                        </span>
                        <button
                          type="button"
                          onClick={() => moveRole(rule.leave_type_id, index, -1)}
                          disabled={index === 0}
                          className="ml-1 text-slate-500 hover:text-slate-900 disabled:opacity-30"
                          aria-label={`Move ${role} earlier`}
                        >
                          ↑
                        </button>
                        <button
                          type="button"
                          onClick={() => moveRole(rule.leave_type_id, index, 1)}
                          disabled={index === rule.approval_chain.length - 1}
                          className="text-slate-500 hover:text-slate-900 disabled:opacity-30"
                          aria-label={`Move ${role} later`}
                        >
                          ↓
                        </button>
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
