from datetime import datetime, date
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field, constr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user, require_role
from app.db.database import get_db
from app.models.employee import Employee
from app.models.holiday import Holiday
from app.models.leave_application import LeaveApplication
from app.models.leave_application_document import LeaveApplicationDocument
from app.models.leave_application_step import LeaveApplicationStep
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.leave_type_approval_step import LeaveTypeApprovalStep
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


def resolve_employee_id(db, current_user):
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if employee is not None:
        return employee.id
    return getattr(current_user, "id", None)


def get_current_step(db, leave):
    return (
        db.query(LeaveApplicationStep)
        .filter(
            LeaveApplicationStep.leave_application_id == leave.id,
            LeaveApplicationStep.status == "PENDING",
        )
        .first()
    )


def _pending_leaves_for_role(db, role):
    return (
        db.query(LeaveApplication)
        .join(
            LeaveApplicationStep,
            LeaveApplicationStep.leave_application_id == LeaveApplication.id,
        )
        .filter(
            LeaveApplication.status == "PENDING",
            LeaveApplicationStep.status == "PENDING",
            LeaveApplicationStep.approver_role == role,
        )
    )


@router.post("/apply", response_model=LeaveApplicationRead)
def apply_leave(
    payload: LeaveApplyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role not in {"EMPLOYEE", "MANAGER", "HR"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only employees, managers, or HR may apply for leave.",
        )

    employee_id = resolve_employee_id(db, current_user)
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

    approval_steps = []
    if current_user.role == "EMPLOYEE":
        configured_steps = (
            db.query(LeaveTypeApprovalStep)
            .filter(LeaveTypeApprovalStep.leave_type_id == payload.leave_type_id)
            .order_by(LeaveTypeApprovalStep.step_order)
            .all()
        )
        if not configured_steps:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No approval flow is configured for this leave type.",
            )
        approval_steps = [step.approver_role for step in configured_steps]
    else:
        approval_steps = ["ADMIN"]

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

    for step_order, approver_role in enumerate(approval_steps, start=1):
        db.add(
            LeaveApplicationStep(
                leave_application_id=leave.id,
                step_order=step_order,
                approver_role=approver_role,
                status="PENDING" if step_order == 1 else "WAITING",
            )
        )
    db.commit()

    return leave


@router.get("/my", response_model=List[LeaveApplicationRead])
def get_my_leaves(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee_id = resolve_employee_id(db, current_user)
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
    employee_id = resolve_employee_id(db, current_user)
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
    employee_id = resolve_employee_id(db, current_user)
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
    current_user=Depends(require_role(["MANAGER", "HR", "ADMIN"])),
):
    leaves = _pending_leaves_for_role(db, current_user.role).all()
    return leaves


@router.get("/pending-count")
def get_pending_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role not in {"MANAGER", "HR", "ADMIN"}:
        return {"count": 0}

    count = _pending_leaves_for_role(db, current_user.role).count()
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
    employee_id = resolve_employee_id(db, current_user)
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
    employee_id = resolve_employee_id(db, current_user)
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
    current_user=Depends(require_role(["MANAGER", "HR", "ADMIN"])),
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

    if resolve_employee_id(db, current_user) == leave.employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot decide on your own leave request.",
        )

    current_step = get_current_step(db, leave)
    if current_step is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active approval step found for this leave request.",
        )

    if current_user.role != current_step.approver_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only {current_step.approver_role} can decide on this leave request at its current stage.",
        )

    current_step.status = decision
    current_step.decided_by = resolve_employee_id(db, current_user)
    current_step.comment = payload.comment
    current_step.decided_at = datetime.utcnow()

    if decision == "REJECTED":
        leave.status = "REJECTED"
        leave.approver_id = resolve_employee_id(db, current_user)
        leave.approver_comment = payload.comment
        leave.decided_at = datetime.utcnow()
    else:
        next_step = (
            db.query(LeaveApplicationStep)
            .filter(
                LeaveApplicationStep.leave_application_id == leave.id,
                LeaveApplicationStep.step_order == current_step.step_order + 1,
            )
            .first()
        )
        if next_step is not None:
            next_step.status = "PENDING"
        else:
            leave.status = "APPROVED"
            leave.approver_id = resolve_employee_id(db, current_user)
            leave.approver_comment = payload.comment
            leave.decided_at = datetime.utcnow()

            balance = get_or_create_balance(db, leave.employee_id, leave.leave_type_id, leave.start_date.year)
            balance.used = balance.used + int(leave.days_count)
            db.add(balance)

    db.commit()
    db.refresh(leave)
    return leave


def _get_sick_leave_or_404(db, leave_id, employee_id):
    leave = db.query(LeaveApplication).filter(LeaveApplication.id == leave_id).first()
    if not leave or leave.employee_id != employee_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found.")

    leave_type = db.query(LeaveType).filter(LeaveType.id == leave.leave_type_id).first()
    if not leave_type or leave_type.name != "Sick Leave":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document upload is only available for Sick Leave requests.",
        )

    return leave


@router.post("/{leave_id}/document", status_code=status.HTTP_201_CREATED)
async def upload_leave_document(
    leave_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee_id = resolve_employee_id(db, current_user)
    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine employee identity.",
        )

    leave = _get_sick_leave_or_404(db, leave_id, employee_id)

    if leave.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A document can only be uploaded while the leave request is pending.",
        )

    file_data = await file.read()

    document = (
        db.query(LeaveApplicationDocument)
        .filter(LeaveApplicationDocument.leave_application_id == leave.id)
        .first()
    )
    if document is None:
        document = LeaveApplicationDocument(leave_application_id=leave.id)

    document.filename = file.filename or "document"
    document.content_type = file.content_type or "application/octet-stream"
    document.file_data = file_data

    db.add(document)
    db.commit()
    db.refresh(document)

    return {"id": document.id, "filename": document.filename, "content_type": document.content_type}


@router.get("/{leave_id}/document")
def get_leave_document(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee_id = resolve_employee_id(db, current_user)
    if employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to determine employee identity.",
        )

    leave = db.query(LeaveApplication).filter(LeaveApplication.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found.")

    is_owner = leave.employee_id == employee_id
    if current_user.role != "MANAGER" and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a manager or the leave's owner can view this document.",
        )

    document = (
        db.query(LeaveApplicationDocument)
        .filter(LeaveApplicationDocument.leave_application_id == leave.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No document uploaded for this leave request.")

    return Response(
        content=document.file_data,
        media_type=document.content_type,
        headers={"Content-Disposition": f'inline; filename="{document.filename}"'},
    )
