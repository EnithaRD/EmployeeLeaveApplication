from pydantic import BaseModel


class LeaveBalanceBase(BaseModel):
    employee_id: int
    leave_type_id: int
    year: int
    allocated: int = 0
    used: int = 0


class LeaveBalanceCreate(LeaveBalanceBase):
    pass


class LeaveBalanceUpdate(BaseModel):
    year: int | None = None
    allocated: int | None = None
    used: int | None = None


class LeaveBalanceRead(LeaveBalanceBase):
    id: int

    model_config = {
        "from_attributes": True,
    }
