from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.leave_application import LeaveApplication
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType


def get_or_create_balance(db: Session, employee_id: int, leave_type_id: int, year: int) -> LeaveBalance:
    balance = (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type_id == leave_type_id,
            LeaveBalance.year == year,
        )
        .first()
    )
    if balance:
        return balance

    leave_type = db.query(LeaveType).filter(LeaveType.id == leave_type_id).first()
    allocated = leave_type.default_annual_quota if leave_type else 0

    balance = LeaveBalance(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        year=year,
        allocated=allocated,
        used=0,
    )
    db.add(balance)
    db.commit()
    db.refresh(balance)
    return balance


def get_available_days(db: Session, employee_id: int, leave_type_id: int, year: int) -> float:
    balance = get_or_create_balance(db, employee_id, leave_type_id, year)

    pending_days = (
        db.query(func.coalesce(func.sum(LeaveApplication.days_count), 0))
        .filter(
            LeaveApplication.employee_id == employee_id,
            LeaveApplication.leave_type_id == leave_type_id,
            LeaveApplication.status == "PENDING",
        )
        .scalar()
    )

    pending_value = float(pending_days) if pending_days is not None else 0.0
    return float(balance.allocated - balance.used - pending_value)


def calculate_working_days(start_date: date, end_date: date, holiday_dates: Iterable[date]) -> int:
    if start_date > end_date:
        return 0

    holiday_set = set(holiday_dates)
    working_days = 0
    current_date = start_date

    while current_date <= end_date:
        is_weekend = current_date.weekday() >= 5
        if not is_weekend and current_date not in holiday_set:
            working_days += 1
        current_date += timedelta(days=1)

    return working_days

