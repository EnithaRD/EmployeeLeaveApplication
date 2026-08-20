from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, constr


class LeaveApplicationBase(BaseModel):
    employee_id: int
    leave_type_id: int | None = None
    start_date: date
    end_date: date
    days_count: Decimal
    reason: str | None = None
    status: constr(max_length=20) | None = None
    approver_id: int | None = None
    approver_comment: str | None = None
    decided_at: datetime | None = None


class LeaveApplicationCreate(LeaveApplicationBase):
    status: str | None = "PENDING"


class LeaveApplicationUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    days_count: Decimal | None = None
    reason: str | None = None
    status: str | None = None
    approver_id: int | None = None
    approver_comment: str | None = None
    decided_at: datetime | None = None


class LeaveApplicationRead(LeaveApplicationBase):
    id: int
    applied_at: datetime

    model_config = {
        "from_attributes": True,
    }
