const MONTH_LABELS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

function computeMaxTotal(data) {
  const max = data.reduce((acc, row) => Math.max(acc, row.approved + row.rejected), 0)
  return max || 1
}

function StackedBar({ row, maxTotal }) {
  const approvedHeight = (row.approved / maxTotal) * 100
  const rejectedHeight = (row.rejected / maxTotal) * 100

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="flex h-40 w-8 flex-col justify-end overflow-hidden rounded-md bg-slate-100">
        <div
          className="w-full bg-rose-500"
          style={{ height: `${rejectedHeight}%` }}
          title={`Rejected: ${row.rejected}`}
        />
        <div
          className="w-full bg-emerald-500"
          style={{ height: `${approvedHeight}%` }}
          title={`Approved: ${row.approved}`}
        />
      </div>
      <span className="text-xs text-slate-500">{MONTH_LABELS[row.month - 1]}</span>
    </div>
  )
}

function ChartLegend() {
  return (
    <div className="flex items-center gap-4 text-xs text-slate-600">
      <span className="flex items-center gap-1">
        <span className="h-3 w-3 rounded-sm bg-emerald-500" /> Approved
      </span>
      <span className="flex items-center gap-1">
        <span className="h-3 w-3 rounded-sm bg-rose-500" /> Rejected
      </span>
    </div>
  )
}

export default function MonthlyLeaveStackedChart({ data }) {
  if (!data || data.length === 0) {
    return <div className="text-sm text-slate-500">No leave request data available.</div>
  }

  const maxTotal = computeMaxTotal(data)

  return (
    <div className="space-y-4">
      <ChartLegend />
      <div className="flex items-end justify-between gap-2 overflow-x-auto pb-2">
        {data.map((row) => (
          <StackedBar key={row.month} row={row} maxTotal={maxTotal} />
        ))}
      </div>
    </div>
  )
}
