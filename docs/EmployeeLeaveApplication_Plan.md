# EmployeeLeaveApplication — Full Project Plan

**Stack:** React.js + Tailwind CSS (frontend) · FastAPI (backend) · PostgreSQL (database)
**Team:** Enitha + Varsha
**Goal:** ERP-style simple Employee Leave Management System, built via vibe coding (Claude for planning/skeleton → ChatGPT/Gemini for continued code generation)

---

## 0. HOW TO USE THIS DOCUMENT

1. Do steps in **Section 3 (Folder Structure)**, **Section 4 (Git Strategy)**, and **Section 5 (Setup Commands)** yourself, locally, right now — before opening ChatGPT/Gemini.
2. Run the SQL in **Section 6** against Postgres to create the database.
3. Go to ChatGPT or Gemini. Paste **Prompt 0 (Handover Prompt)** first, every time you start a new chat session there. This gives it full context so it doesn't hallucinate a different stack/structure.
4. Then paste the numbered prompts **one at a time**, in order, waiting for each to finish before pasting the next. Each prompt tells you which branch to be on before pasting it.
5. Enitha and Varsha work on separate branches in parallel (see Section 2 and 4) so they don't block each other.

---

## 1. BUSINESS REQUIREMENTS DOCUMENT (BRD)

### 1.1 Purpose
Build a simple ERP-style web application that lets employees apply for leave, track their leave balance, and lets managers/admins approve or reject leave requests — as a vibe-coding practice project.

### 1.2 Scope
In scope:
- Employee login and profile
- Leave application, cancellation, and history
- Leave balance tracking by leave type
- Manager/Admin approval workflow
- Admin: manage employees, departments, leave types, holidays
- Simple dashboard with summary cards

Out of scope (v1):
- Payroll integration
- Email/SMS notifications
- Mobile app
- Multi-company / multi-tenant support

### 1.3 User Roles
| Role | Description | Key Actions |
|---|---|---|
| Employee | Regular staff | Apply leave, view balance, view own history, cancel pending leave |
| Manager | Team lead | All Employee actions + approve/reject leave for their team |
| Admin | HR/System admin | All actions + manage employees, departments, leave types, holidays, view all leaves |

### 1.4 Functional Requirements
1. **Auth**: Login with email/password, JWT-based session, role-based access control.
2. **Employee Management**: CRUD for employees (Admin only), assign department & manager.
3. **Leave Types**: Admin defines leave types (Sick, Casual, Earned/Annual, etc.) with default annual quota.
4. **Leave Application**: Employee selects leave type, date range, reason; system validates against available balance and holidays.
5. **Approval Workflow**: Status flow `PENDING → APPROVED / REJECTED / CANCELLED`. Manager approves/rejects with optional comment.
6. **Leave Balance**: Auto-calculated per employee per leave type per year (Allocated − Used − Pending).
7. **Holiday Calendar**: Admin maintains list of company holidays; leave applications skip weekends/holidays in day-count.
8. **Dashboard**: Employee sees balance summary + recent requests. Manager/Admin sees team-wide pending approvals count.

### 1.5 Non-Functional Requirements
- Responsive UI (desktop-first, mobile-usable) using Tailwind CSS.
- REST API, JSON responses, documented via FastAPI's auto-generated `/docs` (Swagger).
- Passwords hashed (bcrypt via passlib), JWT for stateless auth.
- PostgreSQL as the single source of truth; SQLAlchemy ORM + Alembic for migrations.
- Codebase split cleanly into `backend/` and `frontend/` so two people can work independently.

### 1.6 Tech Stack (confirmed)
- **Frontend**: React.js (Vite), Tailwind CSS, React Router, Axios
- **Backend**: FastAPI, SQLAlchemy, Pydantic, Alembic, python-jose (JWT), passlib (bcrypt)
- **Database**: PostgreSQL
- **Version control**: Git + GitHub

---

## 2. TEAM SPLIT — ENITHA & VARSHA

To avoid merge conflicts, split by **module**, not by frontend/backend — each person owns both the API and the UI for their modules end-to-end.

### Enitha — "Identity & Admin" module
- Backend: Auth (login/JWT), Employee CRUD, Department CRUD, Leave Type CRUD, Holiday CRUD
- Frontend: Login page, Employee list/add/edit pages, Admin settings pages (departments, leave types, holidays)
- Owns tables: `users`, `employees`, `departments`, `leave_types`, `holidays`

### Varsha — "Leave Workflow & Dashboard" module
- Backend: Leave application CRUD, approval/rejection endpoints, leave balance calculation
- Frontend: Apply Leave form, My Leaves history page, Manager Approval page, Dashboard (summary cards)
- Owns tables: `leave_balances`, `leave_applications`

### Shared / done together
- Database schema review (Section 6)
- `docs/API_CONTRACTS.md` — both agree on request/response shape before building UI against it
- Final integration on `develop` branch before merging to `main`

---

## 3. FOLDER STRUCTURE

Create this manually (or ask Claude in this chat to scaffold it for you with actual starter files — see note at end).

```
EmployeeLeaveApplication/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── base.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── employee.py
│   │   │   ├── department.py
│   │   │   ├── leave_type.py
│   │   │   ├── leave_application.py
│   │   │   ├── leave_balance.py
│   │   │   └── holiday.py
│   │   ├── schemas/
│   │   │   └── (pydantic schemas, one file per model)
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── auth.py
│   │   │       │   ├── employees.py
│   │   │       │   ├── admin.py
│   │   │       │   └── leaves.py
│   │   │       └── router.py
│   │   └── services/
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── auth/
│   │   │   ├── employee/
│   │   │   ├── admin/
│   │   │   └── leave/
│   │   ├── layouts/
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── hooks/
│   │   ├── context/
│   │   ├── routes/
│   │   └── assets/
│   ├── public/
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── package.json
│
├── docs/
│   ├── BRD.md
│   └── API_CONTRACTS.md
│
├── .gitignore
└── README.md
```

---

## 4. GIT BRANCH STRATEGY

Branches:
- `main` — always deployable, only receives merges from `develop`
- `develop` — integration branch, both of you merge here first
- `feature/enitha-auth-admin` — Enitha's working branch
- `feature/varsha-leave-dashboard` — Varsha's working branch

Rules:
1. Never commit directly to `main`.
2. Create `develop` from `main` once, at the start.
3. Each person branches their `feature/*` off `develop`, **not off main**.
4. Commit and push to your own feature branch as you work through the prompts.
5. When a module is working end-to-end (backend + frontend for that module), open a Pull Request from your feature branch → `develop`. Review each other's PR before merging (even briefly).
6. Once both modules are merged into `develop` and the app works together, merge `develop` → `main`.
7. Pull the latest `develop` into your feature branch (`git pull origin develop`) before starting a new prompt session each day, to avoid drift.

Commands:
```bash
git checkout main
git pull origin main
git checkout -b develop
git push -u origin develop

# Enitha:
git checkout develop
git checkout -b feature/enitha-auth-admin
git push -u origin feature/enitha-auth-admin

# Varsha:
git checkout develop
git checkout -b feature/varsha-leave-dashboard
git push -u origin feature/varsha-leave-dashboard
```

Daily workflow (each person, on their own branch):
```bash
git add .
git commit -m "feat: <short description>"
git push
```

When a module is ready:
```bash
# on GitHub: open PR feature/xxx -> develop, get it reviewed, merge
git checkout develop
git pull origin develop
```

When both modules are merged into develop and tested together:
```bash
git checkout main
git merge develop
git push origin main
```

---

## 5. ENVIRONMENT SETUP COMMANDS

### 5.1 Backend (FastAPI)
```bash
cd EmployeeLeaveApplication
mkdir backend && cd backend
python -m venv venv

# activate:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install fastapi uvicorn[standard] sqlalchemy psycopg2-binary alembic pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] python-multipart python-dotenv

pip freeze > requirements.txt

# run once folders/files exist:
uvicorn app.main:app --reload
```

### 5.2 Frontend (React + Vite + Tailwind)
```bash
cd EmployeeLeaveApplication
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install axios react-router-dom

npm run dev
```

### 5.3 PostgreSQL
```bash
# create the database
psql -U postgres
CREATE DATABASE employee_leave_db;
\q
```

`.env` (in `backend/`, copy from `.env.example`):
```
DATABASE_URL=postgresql://postgres:<your_password>@localhost:5432/employee_leave_db
SECRET_KEY=<generate-a-random-string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## 6. DATABASE SCHEMA (SQL)

Run this against `employee_leave_db` after creating it (or let the backend prompts create it via Alembic — either works; this is here so you understand the shape before coding).

```sql
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(150) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('EMPLOYEE', 'MANAGER', 'ADMIN')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    department_id INTEGER REFERENCES departments(id),
    manager_id INTEGER REFERENCES employees(id),
    date_of_joining DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE leave_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    default_annual_quota INTEGER NOT NULL DEFAULT 0,
    description VARCHAR(255)
);

CREATE TABLE leave_balances (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    leave_type_id INTEGER REFERENCES leave_types(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    allocated INTEGER NOT NULL DEFAULT 0,
    used INTEGER NOT NULL DEFAULT 0,
    UNIQUE(employee_id, leave_type_id, year)
);

CREATE TABLE holidays (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    holiday_date DATE NOT NULL UNIQUE
);

CREATE TABLE leave_applications (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id) ON DELETE CASCADE,
    leave_type_id INTEGER REFERENCES leave_types(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days_count NUMERIC(4,1) NOT NULL,
    reason VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')),
    approver_id INTEGER REFERENCES employees(id),
    approver_comment VARCHAR(500),
    applied_at TIMESTAMP DEFAULT NOW(),
    decided_at TIMESTAMP
);

-- seed data
INSERT INTO leave_types (name, default_annual_quota, description) VALUES
('Sick Leave', 10, 'Medical leave'),
('Casual Leave', 8, 'Short personal leave'),
('Earned Leave', 15, 'Annual/vacation leave');
```

---

## 7. PROMPT SEQUENCE — PASTE ONE BY ONE INTO CHATGPT/GEMINI

### Prompt 0 — Handover Prompt (paste this FIRST, in every new chat)
```
I'm building "EmployeeLeaveApplication", a simple ERP-style Employee Leave
Management System, as a vibe-coding practice project with a teammate.

Confirmed tech stack:
- Frontend: React.js (Vite) + Tailwind CSS + React Router + Axios
- Backend: FastAPI + SQLAlchemy + Pydantic + Alembic + JWT auth (python-jose) + passlib bcrypt
- Database: PostgreSQL

Confirmed folder structure:
EmployeeLeaveApplication/
  backend/app/{main.py, core/, db/, models/, schemas/, api/v1/endpoints/, services/}
  backend/alembic/, backend/tests/, backend/requirements.txt, backend/.env.example
  frontend/src/{components/, pages/, layouts/, services/, hooks/, context/, routes/, assets/}
  docs/

Confirmed database schema (already created in Postgres):
departments, users, employees, leave_types, leave_balances, holidays, leave_applications
(I'll paste the exact CREATE TABLE statements if you need them.)

Roles: EMPLOYEE, MANAGER, ADMIN.

I am working module by module. From here on, only build what I ask for in
each prompt — don't invent extra features or restructure folders. Confirm
you understand this context, then wait for my next prompt.
```

---

### ENITHA'S PROMPTS — branch: `feature/enitha-auth-admin`

**Prompt E1 — Backend core setup**
```
Set up the FastAPI backend core for EmployeeLeaveApplication using the
folder structure I gave you. Create:
- backend/app/core/config.py — loads DATABASE_URL, SECRET_KEY, ALGORITHM,
  ACCESS_TOKEN_EXPIRE_MINUTES from .env using pydantic-settings
- backend/app/db/database.py — SQLAlchemy engine + SessionLocal + get_db dependency
- backend/app/db/base.py — Base declarative class, import all models here later
- backend/app/main.py — FastAPI() app, CORS middleware allowing http://localhost:5173,
  include a router placeholder
Give me full file contents for each file.
```

**Prompt E2 — User & Employee models + schemas**
```
Now create SQLAlchemy models matching this schema exactly:
[paste the users, employees, departments table SQL from Section 6 here]

Create:
- backend/app/models/user.py, employee.py, department.py
- backend/app/schemas/user.py, employee.py, department.py (Pydantic v2 schemas:
  Base, Create, Update, Read variants)
Give me full file contents.
```

**Prompt E3 — Auth endpoints (JWT)**
```
Implement JWT authentication:
- backend/app/core/security.py — password hashing (bcrypt) + JWT create/decode functions
- backend/app/api/v1/endpoints/auth.py — POST /auth/login (OAuth2PasswordRequestForm,
  returns access_token) and GET /auth/me (returns current user, using a
  get_current_user dependency with role available)
Include the get_current_user and a require_role() dependency I can reuse
for role-based access control on other endpoints.
```

**Prompt E4 — Employee & Admin CRUD endpoints**
```
Create backend/app/api/v1/endpoints/employees.py and admin.py:
- employees.py: GET /employees (admin/manager only), GET /employees/{id},
  POST /employees (admin only, also creates the linked user), PUT /employees/{id}
- admin.py: full CRUD for departments, leave_types, and holidays (admin only)
Wire all routers into backend/app/api/v1/router.py and include it in main.py.
```

**Prompt E5 — Frontend auth + layout**
```
In the frontend/src folder, build:
- src/services/api.js — Axios instance with baseURL http://localhost:8000/api/v1,
  attaches JWT from localStorage to headers
- src/context/AuthContext.jsx — login(), logout(), current user state
- src/pages/auth/Login.jsx — Tailwind-styled login form
- src/layouts/MainLayout.jsx — sidebar nav (Dashboard, My Leaves, Employees [admin],
  Admin Settings [admin]) + topbar with logout
- src/routes/index.jsx — React Router setup with protected routes based on role
Use clean, minimal Tailwind styling — no external UI kit.
```

**Prompt E6 — Frontend Employee & Admin pages**
```
Build these pages (Tailwind styled, calling the API via src/services/api.js):
- src/pages/employee/EmployeeList.jsx — table of employees, admin only,
  link to add/edit
- src/pages/employee/EmployeeForm.jsx — add/edit employee form
- src/pages/admin/Departments.jsx, LeaveTypes.jsx, Holidays.jsx — simple
  list + add/edit/delete for each, admin only
```

---

### VARSHA'S PROMPTS — branch: `feature/varsha-leave-dashboard`

**Prompt V1 — Leave models + schemas**
```
Create SQLAlchemy models matching this schema exactly:
[paste the leave_types, leave_balances, leave_applications table SQL from
Section 6 here]

Create:
- backend/app/models/leave_type.py, leave_balance.py, leave_application.py
- backend/app/schemas/leave_type.py, leave_balance.py, leave_application.py
  (Pydantic v2: Base, Create, Update, Read variants)
Note: leave_type.py model may already exist from a teammate's branch —
if so, just reuse the same field names: id, name, default_annual_quota, description.
```

**Prompt V2 — Leave balance calculation service**
```
Create backend/app/services/leave_balance_service.py with:
- get_or_create_balance(db, employee_id, leave_type_id, year) — creates a
  leave_balances row using leave_types.default_annual_quota if missing
- get_available_days(db, employee_id, leave_type_id, year) — returns
  allocated - used - pending (pending = sum of days_count for that
  employee/type with status PENDING)
- a helper calculate_working_days(start_date, end_date, holiday_dates) that
  excludes weekends and holidays
```

**Prompt V3 — Leave application endpoints**
```
Create backend/app/api/v1/endpoints/leaves.py:
- POST /leaves/apply — employee applies for leave; validates available
  balance using leave_balance_service, sets status=PENDING
- GET /leaves/my — employee's own leave history
- PUT /leaves/{id}/cancel — employee cancels own PENDING leave
- GET /leaves/pending — manager/admin sees pending leaves for their team
- PUT /leaves/{id}/decide — manager/admin approves/rejects with comment;
  on approval, increments leave_balances.used
Use the get_current_user and require_role dependencies from auth.py
(assume they exist at backend/app/api/v1/endpoints/auth.py).
```

**Prompt V4 — Frontend: Apply Leave + My Leaves**
```
Build these pages (Tailwind, using src/services/api.js and AuthContext —
assume both already exist from a teammate's branch):
- src/pages/leave/ApplyLeave.jsx — form: leave type dropdown, date range
  picker, reason textarea, shows available balance for selected type
- src/pages/leave/MyLeaves.jsx — table of the employee's leave history with
  status badges (Pending=yellow, Approved=green, Rejected=red, Cancelled=gray)
  and a Cancel button for pending ones
```

**Prompt V5 — Frontend: Manager Approval + Dashboard**
```
Build:
- src/pages/leave/Approvals.jsx — manager/admin view: table of pending
  leave requests with Approve/Reject buttons (reject opens a small comment
  input)
- src/pages/leave/Dashboard.jsx — summary cards: leave balance per type
  (employee view), and pending-approvals count card (manager/admin view,
  conditionally rendered based on role)
```

---

### JOINT — after both branches are merged into `develop`

**Prompt J1 — Integration smoke test**
```
Here is my current repo structure: [paste output of your folder tree, e.g.
`tree -L 4 -I 'node_modules|venv'`]. Both auth/admin and leave/dashboard
modules are built. Review for any endpoint naming mismatches between what
the leave endpoints expect from auth (get_current_user, require_role) and
what auth.py actually exports, and flag anything that won't wire together.
```

---

## 8. NOTE ON GETTING THE SKELETON FROM CLAUDE FIRST

Before you go to ChatGPT/Gemini, you can ask me (Claude), in this same chat,
to actually generate the real starter files for Prompt E1 and V1 above
(config.py, database.py, main.py, the two sets of models) so you commit a
working skeleton to `develop` first — then Enitha and Varsha branch off
something that already runs, instead of both generating `main.py` from
scratch on separate branches. Just say the word and I'll build those files
directly here.
