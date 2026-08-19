# 🌴 Employee Leave Application

_An ERP-style leave management system — because "just email your manager" doesn't scale._

An internal-tool-style web app where employees apply for leave and track their balance, managers approve or reject requests, and admins run the whole show — departments, leave types, holidays, the works. Built full-stack (React + FastAPI + PostgreSQL) as a hands-on practice project for a two-person team, with AI pair-programming baked into the workflow.

---

## ✨ What it actually does

**As an Employee**
- Log in and see your leave balance by type (Sick, Casual, Earned, ...) at a glance
- Apply for leave with a date range + reason — weekends and holidays are automatically excluded from the day count
- Get blocked before you overdraw your balance, not after
- Track the status of every request you've ever filed, and cancel the ones still pending
- Sign in with a password, or skip it entirely with a one-time code emailed to you

**As a Manager**
- See every pending request from people who report to you
- Approve or reject with an optional comment
- Balances update automatically the moment you approve — no spreadsheet math

**As an Admin**
- Onboard employees, assign them to departments and managers
- Define leave types and their annual quotas
- Maintain the company holiday calendar so day-counting stays accurate
- Get a bird's-eye view of every request across the company
- Dashboard chart of approved vs. rejected requests, month by month

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| **Frontend** | React 19, Vite, Tailwind CSS 4, React Router, Axios |
| **Backend** | FastAPI, SQLAlchemy 2, Pydantic v2, Alembic (migrations) |
| **Auth** | JWT (python-jose), Passlib + bcrypt, email OTP login |
| **Database** | PostgreSQL |
| **Testing** | Pytest, pytest-cov, httpx |

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL running locally (or a connection string to one)

### Backend

    cd backend
    python -m venv venv
    venv\Scripts\activate          # Windows
    pip install -r requirements.txt

Create a `.env` file in `backend/` with:

    DATABASE_URL=postgresql://user:password@localhost:5432/leave_app
    SECRET_KEY=your-secret-key
    # Optional — only needed for email OTP login
    SMTP_USERNAME=you@gmail.com
    SMTP_PASSWORD=your-app-password
    SMTP_FROM_EMAIL=you@gmail.com

Run migrations and start the server:

    alembic upgrade head
    uvicorn app.main:app --reload

Backend runs at `http://localhost:8000` (docs at `/docs`).

### Frontend

    cd frontend
    npm install
    npm run dev

Frontend runs at `http://localhost:5173`.

---

## 📁 Project Structure

    backend/
      app/
        api/        # FastAPI route endpoints
        core/        # config, security, email
        models/      # SQLAlchemy models
        schemas/     # Pydantic schemas
        services/    # business logic (balances, approvals, etc.)
      alembic/      # DB migrations
      tests/        # pytest suite

    frontend/
      src/
        pages/       # auth, leave, dashboard pages
        components/  # shared UI
        context/     # auth/app state
        services/    # API clients
        routes/       # route guards by role

    docs/          # PRD, architecture notes, implementation memos

---

## 🗺️ What's not here (yet)

By design, this v1 skips: email/SMS notifications for decisions, payroll/attendance integration, multi-tenant support, and a mobile app. Self-signup is also intentionally out — accounts are admin-provisioned only, like a real internal HR tool.

---

## 👥 Team

- **Enitha** — Identity & Admin
- **Varsha** — Leave Workflow & Dashboard
