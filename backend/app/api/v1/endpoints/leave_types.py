from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.leave_type import LeaveType
from app.models.leave_type_approval_step import LeaveTypeApprovalStep
from app.schemas.leave_type import LeaveTypeRead

router = APIRouter(prefix="/leave-types", tags=["leave_types"])

@router.get("", response_model=List[LeaveTypeRead])
def list_leave_types(db: Session = Depends(get_db)):
    leave_types = (
        db.query(LeaveType)
        .join(LeaveTypeApprovalStep, LeaveTypeApprovalStep.leave_type_id == LeaveType.id)
        .filter(LeaveType.is_active.is_(True))
        .distinct()
        .all()
    )
    return leave_types
