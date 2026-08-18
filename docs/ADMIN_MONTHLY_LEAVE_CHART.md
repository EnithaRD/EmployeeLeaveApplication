# Admin Monthly Leave Chart

**Implementation memo** &middot; Employee Leave Application &middot; backend + frontend
Date: 18 Aug 2026 &middot; New dependencies: none

How the admin Dashboard traded a meaningless "Leave Balances" card (admins can't apply for leave) for a stacked bar chart of approved-vs-rejected leave requests per month.

## Contents

1. [Why & scope](#1-why--scope)
2. [Endpoint](#2-endpoint)
3. [File manifest](#3-file-manifest)
4. [Testing](#4-testing)
5. [Try it against a running server](#5-try-it-against-a-running-server)
6. [Open items](#6-open-items)

## 1. Why & scope

`ADMIN` users saw the same "Leave Balances" card as `EMPLOYEE`/`MANAGER` on the Dashboard, but admins never apply for leave, so it always rendered "No leave balances available." The ask: replace it, for `ADMIN` only, with a chart showing — per month, for 2026 — how many leave requests were approved vs. rejected. Pending/cancelled requests aren't part of the picture; this is about decided requests only, counted by request (not by day, not by distinct employee).

Nothing about the `EMPLOYEE`/`MANAGER` dashboard changed — the balances card and pending-approvals card render exactly as before for those roles.

## 2. Endpoint

### `GET /api/v1/leaves/monthly-summary`

`ADMIN`-only (`require_role(["ADMIN"])`, same guard as `/leaves/decide` and `/leaves/pending`). Returns one entry per calendar month (always 12, zero-filled) with the count of `LeaveApplication` rows whose `status` is `APPROVED` or `REJECTED`, bucketed by the month of `start_date`. `PENDING`/`CANCELLED` requests are excluded entirely.

| Query param | Type | Default | Notes |
|---|---|---|---|
| `year` | `int` | `2026` | Non-integer values (`abc`, `2026.5`, empty) return `422` via FastAPI's normal query validation — no custom parsing. |

**Request:**

```bash
curl "http://localhost:8000/api/v1/leaves/monthly-summary?year=2026" \
  -H "Authorization: Bearer <admin-access-token>"
```

**Response — `200 OK`:**

```json
[
  {"month": 1, "approved": 0, "rejected": 0},
  {"month": 2, "approved": 0, "rejected": 0},
  {"month": 3, "approved": 0, "rejected": 0},
  {"month": 4, "approved": 0, "rejected": 0},
  {"month": 5, "approved": 0, "rejected": 0},
  {"month": 6, "approved": 0, "rejected": 0},
  {"month": 7, "approved": 0, "rejected": 0},
  {"month": 8, "approved": 1, "rejected": 1},
  {"month": 9, "approved": 0, "rejected": 0},
  {"month": 10, "approved": 0, "rejected": 0},
  {"month": 11, "approved": 0, "rejected": 0},
  {"month": 12, "approved": 0, "rejected": 0}
]
```

**Response — `403 Forbidden`** (caller is `EMPLOYEE` or `MANAGER`, not `ADMIN`):

```json
{"detail": "Insufficient permissions"}
```

**Response — `401 Unauthorized`** (missing/invalid/expired bearer token):

```json
{"detail": "Not authenticated"}
```

**Response — `422 Unprocessable Entity`** (`year` isn't a valid integer, e.g. `year=abc`): standard FastAPI/Pydantic query-validation body, same shape every other endpoint in this app returns for a bad query/path param — no custom error handling was added, none was needed.

No new Pydantic response model was introduced: like `GET /leaves/balances`, this endpoint returns hand-built dicts because the payload isn't a 1:1 serialization of one ORM row.

## 3. File manifest

Five files touched — four new, one edited. Nothing outside `backend/app`, `backend/tests`, and `frontend/src`.

| File | | What it does |
|---|---|---|
| `backend/app/services/leave_summary_service.py` | **new** | `get_monthly_status_counts(db, year)` — one grouped query (`extract("month", ...)` + `status`), zero-filled into 12 months. |
| `backend/app/api/v1/endpoints/leaves.py` | edited | Added `GET /monthly-summary`, gated by `require_role(["ADMIN"])`; every existing route untouched. |
| `backend/tests/test_leave_monthly_summary.py` | **new** | Auth gating, correct counting, year filtering, and input-validation edge cases (below). |
| `frontend/src/pages/leave/Dashboard.jsx` | edited | `ADMIN` fetches `/leaves/monthly-summary` instead of `/leaves/balances`; `EMPLOYEE`/`MANAGER` path unchanged. Chart card sits in the same grid row as Pending Approvals. |
| `frontend/src/components/MonthlyLeaveStackedChart.jsx` | **new** | Dependency-free stacked bar chart — CSS height percentages, no charting library. |

## 4. Testing

- **60/60** backend tests passing (`pytest`, run from `backend/`)
- **12** new tests in `test_leave_monthly_summary.py`, **0** pre-existing tests touched or broken

Coverage: `401` with no token, `403` for `EMPLOYEE` and `MANAGER`, correct `APPROVED`/`REJECTED`-only counting per month (`PENDING`/`CANCELLED` excluded), `year` filtering, default year, non-numeric/decimal/empty `year` → `422`, negative/zero `year` → `200` with all-zero counts, and a year-boundary case confirming `2025-12-31`/`2027-01-01` leaves don't leak into `2026`'s totals.

```bash
# run it, from backend/, PowerShell or Git Bash
venv/Scripts/python -m pytest -v
```

Frontend has no test runner configured in this repo (`frontend/package.json` has no test dependency); verification was manual — see below.

## 5. Try it against a running server

```bash
# log in as the seeded admin
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password" \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl "http://localhost:8000/api/v1/leaves/monthly-summary?year=2026" \
  -H "Authorization: Bearer $TOKEN"
```

Also verified visually in the browser (Chrome DevTools automation): logged in as `admin`/`password`, confirmed the chart renders with correct stacked heights against real seeded data, no Leave Balances card appears for `ADMIN`, and the `EMPLOYEE` dashboard is unchanged.

## 6. Open items

- **Hardcoded default year.** `year` defaults to `2026` per the current ask ("for now, only 2026"); the frontend passes it explicitly as `SUMMARY_YEAR` in `Dashboard.jsx` rather than a year picker — extending to other years just means adding a selector, the endpoint already accepts any `year`.
- **No caching.** Every dashboard load re-runs the grouped query; fine at this data volume, would need attention if `leave_applications` grows large.
- **`@app.on_event` is deprecated.** Pre-existing FastAPI warning, unrelated to this change — noted, not fixed.

---

*Employee Leave Application &middot; backend/app + frontend/src &middot; written after implementing and testing the change described above.*
