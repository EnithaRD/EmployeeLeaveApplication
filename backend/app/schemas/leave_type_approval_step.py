from pydantic import BaseModel


class ApprovalStepRead(BaseModel):
    step_order: int
    approver_role: str

    model_config = {
        "from_attributes": True,
    }


class ApprovalFlowRead(BaseModel):
    leave_type_id: int
    leave_type_name: str
    steps: list[ApprovalStepRead]


class ApprovalFlowUpdateRequest(BaseModel):
    steps: list[str]
