from datetime import date

from app.models.employee import Employee
from app.models.leave_application import LeaveApplication
from app.models.leave_type import LeaveType
from app.services.leave_balance_service import (
    calculate_working_days,
    get_available_days,
    get_or_create_balance,
)


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
    employee = Employee(id=1, email="a@example.com", full_name="A", role="EMPLOYEE")
    leave_type = LeaveType(id=1, name="Annual", default_annual_quota=18)
    db_session.add_all([employee, leave_type])
    db_session.commit()

    balance = get_or_create_balance(db_session, employee_id=1, leave_type_id=1, year=2026)

    assert balance.allocated == 18
    assert balance.used == 0


def test_get_or_create_balance_returns_existing(db_session):
    employee = Employee(id=1, email="a@example.com", full_name="A", role="EMPLOYEE")
    leave_type = LeaveType(id=1, name="Annual", default_annual_quota=18)
    db_session.add_all([employee, leave_type])
    db_session.commit()

    first = get_or_create_balance(db_session, employee_id=1, leave_type_id=1, year=2026)
    first.used = 5
    db_session.commit()

    second = get_or_create_balance(db_session, employee_id=1, leave_type_id=1, year=2026)

    assert second.id == first.id
    assert second.used == 5


def test_get_available_days_subtracts_used_and_pending(db_session):
    employee = Employee(id=1, email="a@example.com", full_name="A", role="EMPLOYEE")
    leave_type = LeaveType(id=1, name="Annual", default_annual_quota=18)
    db_session.add_all([employee, leave_type])
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
