from datetime import datetime, date
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, constr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user, require_role
from app.db.database import get_db
from app.models.holiday import Holiday
from app.models.leave_application import LeaveApplication
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.user import User
from app.services.leave_balance_service import (
    calculate_working_days,
    get_available_days,
    get_or_create_balance,
)
from app.services.leave_summary_service import get_monthly_status_counts
from app.schemas.leave_application import LeaveApplicationRead

router = APIRouter(prefix="/leaves", tags=["leaves"])


class LeaveApplyRequest(BaseModel):
    leave_type_id: int
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveDecisionRequest(BaseModel):
    action: constr(to_lower=False, strip_whitespace=True)
    comment: str | None = None


def resolve_employee_id(current_user):
    employee_id = getattr(current_user, "employee_id", None)
    if employee_id is None:
        employee_id = getattr(current_user, "id", None)
    return employee_id


def get_requester_role(db, leave):
    requester = db.query(User).filter(User.id == leave.employee_id).first()
    return requester.role if requester else None


def _pending_leaves_for(db, current_user):
    target_role = "EMPLOYEE" if current_user.role == "MANAGER" else "MANAGER"
    return (
        db.query(LeaveApplication)
        .join(User, User.id == LeaveApplication.employee_id)
        .filter(LeaveApplication.status == "PENDING", User.role == target_role)
    )


@router.post("/apply", response_model=LeaveApplicationRead)
def apply_leave(
    payload: LeaveApplyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role not in {"EMPLOYEE", "MANAGER"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees or managers may apply for leave.",
        )

    employee_id = resolve_employee_id(current_user)
    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine employee identity.",
        )

    if payload.start_date > payload.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be on or before end_date.",
        )

    holidays = (
        db.query(Holiday)
        .filter(Holiday.holiday_date.between(payload.start_date, payload.end_date))
        .all()
    )
    holiday_dates = [holiday.holiday_date for holiday in holidays]
    days_count = calculate_working_days(payload.start_date, payload.end_date, holiday_dates)

    if days_count <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected date range does not contain any working days.",
        )

    available = get_available_days(db, employee_id, payload.leave_type_id, payload.start_date.year)
    if available < days_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient available leave balance. Requested {days_count}, available {available}.",
        )

    leave = LeaveApplication(
        employee_id=employee_id,
        leave_type_id=payload.leave_type_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        days_count=Decimal(days_count),
        reason=payload.reason,
        status="PENDING",
        applied_at=datetime.utcnow(),
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return leave


@router.get("/my", response_model=List[LeaveApplicationRead])
def get_my_leaves(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee_id = resolve_employee_id(current_user)
    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine employee identity.",
        )

    leaves = db.query(LeaveApplication).filter(LeaveApplication.employee_id == employee_id).all()
    return leaves


@router.put("/{leave_id}/cancel", response_model=LeaveApplicationRead)
def cancel_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee_id = resolve_employee_id(current_user)
    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine employee identity.",
        )

    leave = db.query(LeaveApplication).filter(LeaveApplication.id == leave_id).first()
    if not leave or leave.employee_id != employee_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found.")

    if leave.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending leave requests can be cancelled.",
        )

    leave.status = "CANCELLED"
    leave.decided_at = datetime.utcnow()
    db.commit()
    db.refresh(leave)
    return leave


@router.delete("/{leave_id}")
def delete_leave(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee_id = resolve_employee_id(current_user)
    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine employee identity.",
        )

    try:
        leave = db.query(LeaveApplication).filter(LeaveApplication.id == leave_id).first()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete leave request.",
        )

    if not leave or leave.employee_id != employee_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found.")

    if leave.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending leave requests can be deleted.",
        )

    try:
        db.delete(leave)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete leave request.",
        )

    return {"message": "Leave request deleted successfully."}


@router.get("/pending", response_model=List[LeaveApplicationRead])
def get_pending_leaves(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["MANAGER", "ADMIN"])),
):
    leaves = _pending_leaves_for(db, current_user).all()
    return leaves


@router.get("/pending-count")
def get_pending_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role not in {"ADMIN", "MANAGER"}:
        return {"count": 0}

    count = _pending_leaves_for(db, current_user).count()
    return {"count": int(count or 0)}


@router.get("/monthly-summary")
def get_monthly_summary(
    year: int = 2026,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ADMIN"])),
):
    return get_monthly_status_counts(db, year)


@router.get("/balances")
def get_leave_balances(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee_id = resolve_employee_id(current_user)
    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine employee identity.",
        )

    results = (
        db.query(LeaveBalance, LeaveType)
        .join(LeaveType, LeaveBalance.leave_type_id == LeaveType.id)
        .filter(LeaveBalance.employee_id == employee_id)
        .all()
    )

    return [
        {
            "id": balance.id,
            "leave_type_id": balance.leave_type_id,
            "leave_type_name": leave_type.name,
            "year": balance.year,
            "allocated": balance.allocated,
            "used": balance.used,
        }
        for balance, leave_type in results
    ]


@router.get("/available")
def get_available_leave(
    leave_type_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee_id = resolve_employee_id(current_user)
    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine employee identity.",
        )

    available = get_available_days(db, employee_id, leave_type_id, date.today().year)
    return {"available": available}


@router.put("/{leave_id}/decide", response_model=LeaveApplicationRead)
def decide_leave(
    leave_id: int,
    payload: LeaveDecisionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["MANAGER", "ADMIN"])),
):
    decision = payload.action.upper()
    if decision not in {"APPROVED", "REJECTED"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be APPROVED or REJECTED.",
        )

    leave = db.query(LeaveApplication).filter(LeaveApplication.id == leave_id).first()
    if not leave or leave.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending leave request not found.")

    requester_role = get_requester_role(db, leave)

    if requester_role == "EMPLOYEE" and current_user.role != "MANAGER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a manager can decide on an employee's leave request.",
        )

    if requester_role == "MANAGER" and current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an admin can decide on a manager's leave request.",
        )

    leave.status = decision
    leave.approver_id = resolve_employee_id(current_user)
    leave.approver_comment = payload.comment
    leave.decided_at = datetime.utcnow()

    if decision == "APPROVED":
        balance = get_or_create_balance(db, leave.employee_id, leave.leave_type_id, leave.start_date.year)
        balance.used = balance.used + int(leave.days_count)
        db.add(balance)

    db.commit()
    db.refresh(leave)
    return leave
