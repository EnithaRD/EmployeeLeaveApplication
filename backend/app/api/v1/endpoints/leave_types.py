from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.leave_type import LeaveType
from app.schemas.leave_type import LeaveTypeRead

router = APIRouter(prefix="/leave-types", tags=["leave_types"])

@router.get("", response_model=List[LeaveTypeRead])
def list_leave_types(db: Session = Depends(get_db)):
    leave_types = db.query(LeaveType).filter(LeaveType.is_active.is_(True)).all()
    return leave_types
