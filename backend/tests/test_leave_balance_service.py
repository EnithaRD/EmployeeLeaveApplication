from datetime import date

from app.models.employee import Employee
from app.models.leave_application import LeaveApplication
from app.models.leave_type import LeaveType
from app.models.user import User
from app.services.leave_balance_service import (
    calculate_working_days,
    get_available_days,
    get_or_create_balance,
)


def _make_employee(db_session, employee_id: int, email: str) -> Employee:
    user = User(email=email, password="password", role="EMPLOYEE", is_active=True)
    db_session.add(user)
    db_session.flush()

    employee = Employee(
        id=employee_id,
        user_id=user.id,
        full_name="A",
        date_of_joining=date(2026, 1, 1),
    )
    db_session.add(employee)
    return employee


def test_calculate_working_days_excludes_weekends():
    # Mon 2026-08-10 .. Fri 2026-08-14 is a full working week
    start = date(2026, 8, 10)
    end = date(2026, 8, 16)  # includes following Sat/Sun

    assert calculate_working_days(start, end, holiday_dates=[]) == 5


def test_calculate_working_days_excludes_holidays():
    start = date(2026, 8, 10)
    end = date(2026, 8, 14)
    holiday = date(2026, 8, 12)

    assert calculate_working_days(start, end, holiday_dates=[holiday]) == 4


def test_calculate_working_days_start_after_end_returns_zero():
    start = date(2026, 8, 14)
    end = date(2026, 8, 10)

    assert calculate_working_days(start, end, holiday_dates=[]) == 0


def test_get_or_create_balance_creates_with_leave_type_quota(db_session):
    _make_employee(db_session, employee_id=1, email="a@example.com")
    leave_type = LeaveType(id=1, name="Annual", default_annual_quota=18)
    db_session.add(leave_type)
    db_session.commit()

    balance = get_or_create_balance(db_session, employee_id=1, leave_type_id=1, year=2026)

    assert balance.allocated == 18
    assert balance.used == 0


def test_get_or_create_balance_returns_existing(db_session):
    _make_employee(db_session, employee_id=1, email="a@example.com")
    leave_type = LeaveType(id=1, name="Annual", default_annual_quota=18)
    db_session.add(leave_type)
    db_session.commit()

    first = get_or_create_balance(db_session, employee_id=1, leave_type_id=1, year=2026)
    first.used = 5
    db_session.commit()

    second = get_or_create_balance(db_session, employee_id=1, leave_type_id=1, year=2026)

    assert second.id == first.id
    assert second.used == 5


def test_get_available_days_subtracts_used_and_pending(db_session):
    _make_employee(db_session, employee_id=1, email="a@example.com")
    leave_type = LeaveType(id=1, name="Annual", default_annual_quota=18)
    db_session.add(leave_type)
    db_session.commit()

    balance = get_or_create_balance(db_session, employee_id=1, leave_type_id=1, year=2026)
    balance.used = 3
    db_session.add(
        LeaveApplication(
            employee_id=1,
            leave_type_id=1,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 2),
            days_count=2,
            status="PENDING",
        )
    )
    db_session.commit()

    available = get_available_days(db_session, employee_id=1, leave_type_id=1, year=2026)

    assert available == 13  # 18 allocated - 3 used - 2 pending
