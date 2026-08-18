from datetime import date, datetime
from decimal import Decimal

from app.core.security import create_access_token
from app.models.employee import Employee
from app.models.leave_application import LeaveApplication
from app.models.user import User


def _create_user_with_token(db_session, email, role):
    user = User(email=email, password="secret123", role=role, is_active=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    employee = Employee(
        user_id=user.id,
        full_name=email,
        department_id=None,
        manager_id=None,
        date_of_joining=date.today(),
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    token = create_access_token(user_id=user.id, role=user.role)
    headers = {"Authorization": f"Bearer {token}"}
    return user, employee, headers


def _create_leave(db_session, employee_id, leave_status, start_date):
    leave = LeaveApplication(
        employee_id=employee_id,
        leave_type_id=None,
        start_date=start_date,
        end_date=start_date,
        days_count=Decimal("1"),
        reason="test leave",
        status=leave_status,
        applied_at=datetime.utcnow(),
    )
    db_session.add(leave)
    db_session.commit()
    db_session.refresh(leave)
    return leave


def test_monthly_summary_without_auth_returns_401(client):
    response = client.get("/api/v1/leaves/monthly-summary?year=2026")

    assert response.status_code == 401


def test_monthly_summary_as_employee_returns_403(client, db_session):
    _, _, headers = _create_user_with_token(db_session, "employee@example.com", "EMPLOYEE")

    response = client.get("/api/v1/leaves/monthly-summary?year=2026", headers=headers)

    assert response.status_code == 403


def test_monthly_summary_as_manager_returns_403(client, db_session):
    _, _, headers = _create_user_with_token(db_session, "manager@example.com", "MANAGER")

    response = client.get("/api/v1/leaves/monthly-summary?year=2026", headers=headers)

    assert response.status_code == 403


def test_monthly_summary_as_admin_counts_only_approved_and_rejected(client, db_session):
    _, employee, headers = _create_user_with_token(db_session, "admin@example.com", "ADMIN")

    _create_leave(db_session, employee.id, "APPROVED", date(2026, 1, 10))
    _create_leave(db_session, employee.id, "APPROVED", date(2026, 1, 20))
    _create_leave(db_session, employee.id, "REJECTED", date(2026, 1, 15))
    _create_leave(db_session, employee.id, "PENDING", date(2026, 1, 5))
    _create_leave(db_session, employee.id, "CANCELLED", date(2026, 1, 25))
    _create_leave(db_session, employee.id, "REJECTED", date(2026, 3, 2))

    response = client.get("/api/v1/leaves/monthly-summary?year=2026", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12

    january = next(m for m in data if m["month"] == 1)
    march = next(m for m in data if m["month"] == 3)
    february = next(m for m in data if m["month"] == 2)

    assert january == {"month": 1, "approved": 2, "rejected": 1}
    assert march == {"month": 3, "approved": 0, "rejected": 1}
    assert february == {"month": 2, "approved": 0, "rejected": 0}


def test_monthly_summary_filters_by_year(client, db_session):
    _, employee, headers = _create_user_with_token(db_session, "admin2@example.com", "ADMIN")

    _create_leave(db_session, employee.id, "APPROVED", date(2025, 6, 1))
    _create_leave(db_session, employee.id, "APPROVED", date(2026, 6, 1))

    response_2026 = client.get("/api/v1/leaves/monthly-summary?year=2026", headers=headers)
    response_2025 = client.get("/api/v1/leaves/monthly-summary?year=2025", headers=headers)

    june_2026 = next(m for m in response_2026.json() if m["month"] == 6)
    june_2025 = next(m for m in response_2025.json() if m["month"] == 6)

    assert june_2026 == {"month": 6, "approved": 1, "rejected": 0}
    assert june_2025 == {"month": 6, "approved": 1, "rejected": 0}


def test_monthly_summary_default_year_is_2026(client, db_session):
    _, employee, headers = _create_user_with_token(db_session, "admin3@example.com", "ADMIN")

    _create_leave(db_session, employee.id, "APPROVED", date(2026, 9, 1))

    response = client.get("/api/v1/leaves/monthly-summary", headers=headers)

    assert response.status_code == 200
    september = next(m for m in response.json() if m["month"] == 9)
    assert september == {"month": 9, "approved": 1, "rejected": 0}


# --- year query param: wrong type -------------------------------------------------


def test_monthly_summary_with_non_numeric_year_returns_422(client, db_session):
    _, _, headers = _create_user_with_token(db_session, "admin4@example.com", "ADMIN")

    response = client.get("/api/v1/leaves/monthly-summary?year=abc", headers=headers)

    assert response.status_code == 422


def test_monthly_summary_with_decimal_year_returns_422(client, db_session):
    _, _, headers = _create_user_with_token(db_session, "admin5@example.com", "ADMIN")

    response = client.get("/api/v1/leaves/monthly-summary?year=2026.5", headers=headers)

    assert response.status_code == 422


def test_monthly_summary_with_empty_year_returns_422(client, db_session):
    _, _, headers = _create_user_with_token(db_session, "admin6@example.com", "ADMIN")

    response = client.get("/api/v1/leaves/monthly-summary?year=", headers=headers)

    assert response.status_code == 422


# --- year query param: valid-looking but out-of-range values ----------------------


def test_monthly_summary_with_negative_year_returns_200_with_all_zero_counts(client, db_session):
    _, employee, headers = _create_user_with_token(db_session, "admin7@example.com", "ADMIN")

    _create_leave(db_session, employee.id, "APPROVED", date(2026, 1, 1))

    response = client.get("/api/v1/leaves/monthly-summary?year=-1", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12
    assert all(row == {"month": row["month"], "approved": 0, "rejected": 0} for row in data)


def test_monthly_summary_with_zero_year_returns_200_with_all_zero_counts(client, db_session):
    _, _, headers = _create_user_with_token(db_session, "admin8@example.com", "ADMIN")

    response = client.get("/api/v1/leaves/monthly-summary?year=0", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12
    assert all(row == {"month": row["month"], "approved": 0, "rejected": 0} for row in data)


# --- year boundary: adjacent-year leaves must not leak across the boundary --------


def test_monthly_summary_does_not_leak_across_year_boundary(client, db_session):
    _, employee, headers = _create_user_with_token(db_session, "admin9@example.com", "ADMIN")

    _create_leave(db_session, employee.id, "APPROVED", date(2025, 12, 31))
    _create_leave(db_session, employee.id, "REJECTED", date(2027, 1, 1))
    _create_leave(db_session, employee.id, "APPROVED", date(2026, 12, 31))
    _create_leave(db_session, employee.id, "REJECTED", date(2026, 1, 1))

    response = client.get("/api/v1/leaves/monthly-summary?year=2026", headers=headers)

    assert response.status_code == 200
    data = response.json()

    december = next(m for m in data if m["month"] == 12)
    january = next(m for m in data if m["month"] == 1)
    total_approved = sum(row["approved"] for row in data)
    total_rejected = sum(row["rejected"] for row in data)

    assert december == {"month": 12, "approved": 1, "rejected": 0}
    assert january == {"month": 1, "approved": 0, "rejected": 1}
    assert total_approved == 1
    assert total_rejected == 1
