from pydantic import BaseModel, constr


class LeaveTypeBase(BaseModel):
    name: constr(max_length=50)
    default_annual_quota: int = 0
    description: str | None = None
    is_active: bool = True


class LeaveTypeCreate(LeaveTypeBase):
    pass


class LeaveTypeUpdate(BaseModel):
    name: constr(max_length=50) | None = None
    default_annual_quota: int | None = None
    description: str | None = None
    is_active: bool | None = None


class LeaveTypeRead(LeaveTypeBase):
    id: int

    model_config = {
        "from_attributes": True,
    }
