# Product Requirements Document (PRD)
## EmployeeLeaveApplication

| | |
|---|---|
| **Owner** | You (project lead), with Enitha & Varsha |
| **Status** | Draft v1 |
| **Last updated** | 2026-08-12 |
| **Related doc** | `EmployeeLeaveApplication_Plan.md` (BRD, folder structure, git strategy, build prompts) |

---

## 1. Overview

**Product name:** EmployeeLeaveApplication

**One-line description:** A simple ERP-style web app where employees apply for leave and track balances, and managers/admins approve requests — built as a vibe-coding practice project.

**Problem statement:** There's no live product problem here — the "problem" is a learning one: practice building a full-stack app end-to-end (React + Tailwind + FastAPI + Postgres) with a small team, using AI pair-programming (Claude for planning, ChatGPT/Gemini for implementation), while producing something that behaves like a real internal HR tool.

**Why this shape:** Leave management is a well-understood domain (everyone's used one), has a natural multi-role structure (employee/manager/admin), and touches every layer of the stack — auth, CRUD, business-rule validation (balance checks), a simple approval workflow, and a dashboard — without being so large it can't be finished.

---

## 2. Goals & Success Criteria

### 2.1 Goals
1. Ship a working, deployable-quality v1: an employee can log in, apply for leave, and see it get approved or rejected by a manager, with the balance updating correctly.
2. Practice a realistic two-person collaborative git workflow (feature branches → develop → main) without merge chaos.
3. Practice prompting AI tools with structured, scoped requests instead of one giant "build me an app" prompt.

### 2.2 Success Criteria (v1 "done")
- [ ] An Admin can create departments, leave types, holidays, and employees.
- [ ] An Employee can log in, see their leave balance, apply for leave, and see it in "My Leaves" with correct status.
- [ ] A Manager can see pending requests from their team and approve/reject them, with the balance updating on approval.
- [ ] Leave day counts correctly exclude weekends and holidays.
- [ ] The app runs locally end-to-end: `npm run dev` (frontend) + `uvicorn app.main:app --reload` (backend) + Postgres, with no broken flows between Enitha's and Varsha's modules.
- [ ] Code is merged to `main` via reviewed PRs from both contributors.

### 2.3 Non-goals for v1
- Notifications (email/SMS)
- Payroll or attendance integration
- Multi-company/tenant support
- Mobile app / PWA
- Password reset / forgot-password flow (can be a v2 stretch item)

---

## 3. Users & Personas

| Persona | Role in system | Primary needs |
|---|---|---|
| **Employee** (e.g. an individual contributor) | `EMPLOYEE` | See how many leave days are left, apply quickly, know the status of a request |
| **Manager** | `MANAGER` (also an employee) | See who on their team has requested leave, approve/reject with minimal clicks |
| **Admin** (HR/system owner) | `ADMIN` | Full control: onboard employees, configure leave types & holidays, oversight of all requests |

Note: a `MANAGER` is still an `employee` row (has their own leave balance too) — they just additionally have approval rights over employees whose `manager_id` points to them.

---

## 4. User Stories

### Employee
- As an employee, I want to log in with my email/password so that I can access my own leave data.
- As an employee, I want to see my current leave balance by type (Sick, Casual, Earned) so I know what I can apply for.
- As an employee, I want to apply for leave by selecting a type, date range, and reason, so my manager can review it.
- As an employee, I want to be warned if I don't have enough balance before I submit.
- As an employee, I want to see the status of my past and pending requests.
- As an employee, I want to cancel a leave request that's still pending.

### Manager
- As a manager, I want to see all pending leave requests from people who report to me.
- As a manager, I want to approve or reject a request, optionally with a comment, so my team member knows the outcome.
- As a manager, I want approved leave to automatically reduce that employee's balance, without manual math.

### Admin
- As an admin, I want to add/edit/deactivate employees and assign them to a department and a manager.
- As an admin, I want to define leave types and their default annual quota.
- As an admin, I want to maintain a holiday calendar so leave-day calculations are accurate.
- As an admin, I want visibility into all leave requests across the company (not just my own team), for oversight.

---

## 5. Functional Requirements (detailed)

### 5.1 Authentication & Authorization
- Login via email + password → JWT access token (stored client-side, sent as `Authorization: Bearer`).
- Role stored on the `users` row: `EMPLOYEE | MANAGER | ADMIN`.
- Route-level protection: FastAPI dependency `require_role([...])`; frontend route guards hide/redirect pages by role.
- No self-signup — accounts are created by Admin only (this is an internal-tool pattern, matches BRD scope).

### 5.2 Employee Management (Admin)
- Create employee: full name, email (becomes login), department, manager (optional), date of joining, role.
- Edit employee details; deactivate (soft-delete via `users.is_active`, not a hard delete).
- List/search employees, filterable by department.

### 5.3 Leave Types & Holidays (Admin)
- CRUD for leave types: name, default annual quota, description.
- CRUD for holidays: name, date.
- Changing a leave type's default quota does **not** retroactively change already-allocated balances for the current year (avoids silently changing someone's mid-year balance).

### 5.4 Leave Balance
- One `leave_balances` row per (employee, leave_type, year).
- Auto-created on first relevant action (first apply, or first admin view) using the leave type's `default_annual_quota` at that time.
- Available = `allocated − used − pending` (pending = sum of days on that employee/type currently `PENDING`).
- `used` increments only on approval, never on submission.

### 5.5 Leave Application
- Employee selects leave type, start date, end date, reason (required, min length e.g. 5 chars).
- Backend computes `days_count` = working days between start and end, excluding weekends and rows in `holidays`.
- Backend rejects the application (400 error, shown in UI) if `days_count > available balance` for that type/year.
- On success: row inserted with `status = PENDING`.
- Employee can cancel only while `status = PENDING` → sets `status = CANCELLED` (does not affect balance, since it was never counted as `used`).

### 5.6 Approval Workflow
- Manager/Admin sees a list of `PENDING` requests scoped to: Manager → employees where `manager_id = me`; Admin → all.
- Decide action: `APPROVED` or `REJECTED`, optional comment, sets `decided_at`.
- On `APPROVED`: increment `leave_balances.used` by `days_count` for that employee/type/year.
- On `REJECTED`: no balance change.
- A decided request cannot be re-decided (idempotency check).

### 5.7 Dashboard
- Employee view: cards per leave type showing allocated/used/available for the current year; list of most recent 5 requests.
- Manager/Admin view: additionally shows a "Pending Approvals" count card linking to the Approvals page.

---

## 6. Non-Functional Requirements
- **Performance:** trivial at this scale (small team, local dev) — no specific SLA needed, but avoid N+1 query patterns in list endpoints as a good habit.
- **Security:** passwords hashed with bcrypt; JWT secret in `.env`, never committed; role checks enforced server-side (not just hidden in UI).
- **Usability:** every list/table has a visible empty state ("No leave requests yet") rather than a blank screen.
- **Maintainability:** one file per model/schema/endpoint group, matching the folder structure in the companion plan doc, so Enitha and Varsha's modules don't collide.
- **Data integrity:** foreign keys with `ON DELETE CASCADE` only where safe (e.g. deleting a user's employee record); `CHECK` constraints on status/role enums at the DB level as a backstop to app-level validation.

---

## 7. Data Model (summary)

See the companion plan doc for full `CREATE TABLE` SQL. Entities:

- `departments` (id, name)
- `users` (id, email, hashed_password, role, is_active)
- `employees` (id, user_id, full_name, department_id, manager_id, date_of_joining)
- `leave_types` (id, name, default_annual_quota, description)
- `leave_balances` (id, employee_id, leave_type_id, year, allocated, used)
- `holidays` (id, name, holiday_date)
- `leave_applications` (id, employee_id, leave_type_id, start_date, end_date, days_count, reason, status, approver_id, approver_comment, applied_at, decided_at)

Relationships: an `employee` belongs to one `department` and (optionally) one `manager` (self-referencing FK to `employees`). A `leave_application` belongs to one `employee` and one `leave_type`, and is decided by an `approver` (also an `employees.id`).

---

## 8. Key Screens (frontend)

| Screen | Role(s) | Module owner |
|---|---|---|
| Login | All | Enitha |
| Dashboard | All (content varies by role) | Varsha |
| Apply Leave | Employee | Varsha |
| My Leaves | Employee | Varsha |
| Approvals | Manager, Admin | Varsha |
| Employee List / Form | Admin | Enitha |
| Departments / Leave Types / Holidays (Admin settings) | Admin | Enitha |

(Full build prompts for each of these are in `EmployeeLeaveApplication_Plan.md`, Section 7.)

### 8.1 Full Frontend Page Inventory

The frontend skeleton has all 14 pages routed in `App.tsx` and wired into the sidebar nav already — no further routing work is needed; remaining work is filling in forms/tables and connecting each page to its API module.

**Auth (1 page)**

| # | Page | Route | Use Case | Status |
|---|---|---|---|---|
| 1 | Login | `/login` | Employee/Manager/HR sign in with email + password | UI built, not wired to API yet |

**Employee (4 pages)**

| # | Page | Route | Use Case | Status |
|---|---|---|---|---|
| 2 | EmployeeDashboard | `/employee` | Landing page after login — leave balance rings, pending requests, upcoming holiday, recent requests table | UI built with mock data |
| 3 | ApplyLeave | `/employee/apply` | Form to submit a new leave request (leave type, dates, reason) | Placeholder only |
| 4 | LeaveHistory | `/employee/history` | Full list of the employee's past/pending leave applications with status | Placeholder only |
| 5 | HolidaysView | `/employee/holidays` | Read-only list of org holidays for the year | Placeholder only |

**Manager (3 pages)**

| # | Page | Route | Use Case | Status |
|---|---|---|---|---|
| 6 | ManagerDashboard | `/manager` | Landing page — pending approvals count, team size, who's on leave this week | UI built with mock data |
| 7 | TeamRequests | `/manager/requests` | Full list of team leave requests, approve/reject with comments | Placeholder only |
| 8 | TeamCalendar | `/manager/calendar` | Calendar view of team leave/availability | Placeholder only |

**HR/Admin (6 pages)**

| # | Page | Route | Use Case | Status |
|---|---|---|---|---|
| 9 | HRDashboard | `/hr` | Landing page — total employees, on leave today, pending requests, department utilization table | UI built with mock data |
| 10 | EmployeesAdmin | `/hr/employees` | Create/edit employees, assign department & manager | Placeholder only |
| 11 | DepartmentsAdmin | `/hr/departments` | Create/edit departments, assign department manager | Placeholder only |
| 12 | LeaveConfigAdmin | `/hr/leave-config` | Configure leave types (Annual/Sick/Casual) and their policies/quotas | Placeholder only |
| 13 | HolidaysAdmin | `/hr/holidays` | Add/edit org-wide holiday calendar | Placeholder only |
| 14 | ReportsView | `/hr/reports` | Org-wide leave analytics and exportable reports | Placeholder only |

**Status summary:** 4 pages are visually built with mock data (Login + the 3 dashboards) but not yet wired to the API; the other 10 are stub pages waiting on backend endpoints (build order in the companion HANDOVER.md §11).

**Delta from Section 8's original scope:** the page inventory introduces two screens not in the original v1 scope — `TeamCalendar` (manager) and `ReportsView` (HR). These are being treated as in-scope for this build since the skeleton already routes them; see 8.1.1 below for what "done" means for each.

#### 8.1.1 Notes on non-trivial wiring

Most placeholder pages are a straightforward form/table bound to an existing endpoint from Section 5. A few need slightly more:

- **TeamRequests** — approve/reject needs a per-request detail view or modal (not just a flat table), since a comment field is entered per decision.
- **TeamCalendar** — new to scope; needs a `GET` endpoint that returns approved leave spans for an employee's direct reports over a date range, not just an existing CRUD endpoint.
- **ReportsView** — new to scope; needs date-range and department filters, plus an export action (CSV at minimum for v1). Treat as a stretch goal for M4 if time is short — it's the least essential to the core approve/apply loop.

---

## 9. Assumptions
- Single company, single currency of "days" (no half-day granularity beyond what `NUMERIC(4,1)` allows, e.g. 0.5-day leave is supported but not enforced in UI logic for v1).
- Leave year = calendar year (Jan 1–Dec 31); no fiscal-year config.
- No time zone handling beyond the server's local date — acceptable for a practice project with one team in one location.
- Enitha and Varsha have independent local dev environments and their own Postgres instance (or share one dev DB — not specified; assumed independent for this PRD).

## 10. Risks
| Risk | Mitigation |
|---|---|
| Two people's AI-generated code diverges in style/naming | Prompt 0 handover context + shared `docs/API_CONTRACTS.md` locks down field names before UI is built against them |
| Merge conflicts on shared files (e.g. `router.py`, `App.jsx`) | Keep those files thin (just wiring/imports); each person only adds their own lines |
| Balance logic bugs (double-counting pending vs used) | Centralized in one service function (`leave_balance_service.py`), not duplicated across endpoints |
| Scope creep (adding notifications, payroll, etc.) | Explicit Non-goals section (2.3) — anything not listed there is a v2 idea, not a v1 task |

## 11. Milestones (suggested, not fixed)
1. **M1 — Skeleton:** backend boots, frontend boots, DB created, both branches created off `develop`.
2. **M2 — Enitha's module functional:** login works, admin can manage employees/departments/leave types/holidays.
3. **M3 — Varsha's module functional:** employee can apply for leave, manager can approve/reject, balance updates.
4. **M4 — Integration:** both merged to `develop`, dashboard shows real data end-to-end, smoke-tested together.
5. **M5 — v1 complete:** merged to `main`.

## 12. Open Questions
- Should Managers be able to apply for their **own** leave to be approved by someone else (their own manager), or is a Manager always top-of-chain for v1? *(Recommendation: allow `manager_id` on a Manager's own employee row too — Admin approves in that case, since Admin sees all pending requests.)*
- Shared dev database or one each? *(Recommendation: shared local Postgres is simplest for two people testing the same seed data — but each can run their own if preferred.)*
