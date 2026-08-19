from datetime import datetime
from pydantic import BaseModel, field_validator

VALID_APPROVER_ROLES = {"MANAGER", "HR", "ADMIN"}


class ApprovalRoutingRuleRead(BaseModel):
    leave_type_id: int
    leave_type_name: str
    approval_chain: list[str]
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True,
    }


class ApprovalRoutingRuleUpdate(BaseModel):
    approval_chain: list[str]

    @field_validator("approval_chain")
    @classmethod
    def validate_chain(cls, value):
        if not value:
            raise ValueError("approval_chain must contain at least one approver role.")

        normalized = [role.strip().upper() for role in value]
        invalid = [role for role in normalized if role not in VALID_APPROVER_ROLES]
        if invalid:
            raise ValueError(
                f"Invalid approver role(s): {', '.join(invalid)}. "
                f"Allowed roles: {', '.join(sorted(VALID_APPROVER_ROLES))}."
            )

        return normalized
