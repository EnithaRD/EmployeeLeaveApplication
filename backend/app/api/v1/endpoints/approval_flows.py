from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import require_role
from app.db.database import get_db
from app.models.leave_type import LeaveType
from app.models.leave_type_approval_step import LeaveTypeApprovalStep
from app.schemas.leave_type_approval_step import (
    ApprovalFlowRead,
    ApprovalFlowUpdateRequest,
    ApprovalStepRead,
)

router = APIRouter(prefix="/approval-flows", tags=["approval_flows"])

ALLOWED_APPROVER_ROLES = {"MANAGER", "HR"}


@router.get("", response_model=List[ApprovalFlowRead])
def list_approval_flows(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ADMIN"])),
):
    leave_types = db.query(LeaveType).all()

    flows = []
    for leave_type in leave_types:
        steps = (
            db.query(LeaveTypeApprovalStep)
            .filter(LeaveTypeApprovalStep.leave_type_id == leave_type.id)
            .order_by(LeaveTypeApprovalStep.step_order)
            .all()
        )
        flows.append(
            ApprovalFlowRead(
                leave_type_id=leave_type.id,
                leave_type_name=leave_type.name,
                steps=[ApprovalStepRead.model_validate(step) for step in steps],
            )
        )

    return flows


@router.put("/{leave_type_id}", response_model=ApprovalFlowRead)
def update_approval_flow(
    leave_type_id: int,
    payload: ApprovalFlowUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ADMIN"])),
):
    leave_type = db.query(LeaveType).filter(LeaveType.id == leave_type_id).first()
    if not leave_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave type not found.")

    if not payload.steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one approval step is required.",
        )

    invalid_roles = [role for role in payload.steps if role not in ALLOWED_APPROVER_ROLES]
    if invalid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Approver role must be MANAGER or HR.",
        )

    db.query(LeaveTypeApprovalStep).filter(
        LeaveTypeApprovalStep.leave_type_id == leave_type_id
    ).delete()

    for step_order, approver_role in enumerate(payload.steps, start=1):
        db.add(
            LeaveTypeApprovalStep(
                leave_type_id=leave_type_id,
                step_order=step_order,
                approver_role=approver_role,
            )
        )

    db.commit()

    steps = (
        db.query(LeaveTypeApprovalStep)
        .filter(LeaveTypeApprovalStep.leave_type_id == leave_type_id)
        .order_by(LeaveTypeApprovalStep.step_order)
        .all()
    )

    return ApprovalFlowRead(
        leave_type_id=leave_type.id,
        leave_type_name=leave_type.name,
        steps=[ApprovalStepRead.model_validate(step) for step in steps],
    )
