from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import require_role
from app.db.database import get_db
from app.models.approval_routing_rule import ApprovalRoutingRule
from app.models.leave_type import LeaveType
from app.schemas.approval_routing import ApprovalRoutingRuleRead, ApprovalRoutingRuleUpdate
from app.services.approval_routing_service import default_chain_for_name

router = APIRouter(prefix="/admin/approval-routing", tags=["approval-routing"])


def _serialize(leave_type: LeaveType, rule: ApprovalRoutingRule | None) -> ApprovalRoutingRuleRead:
    chain = rule.approval_chain.split(",") if rule else default_chain_for_name(leave_type.name)
    return ApprovalRoutingRuleRead(
        leave_type_id=leave_type.id,
        leave_type_name=leave_type.name,
        approval_chain=chain,
        updated_at=rule.updated_at if rule else None,
    )


@router.get("", response_model=List[ApprovalRoutingRuleRead])
def list_approval_routing(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ADMIN"])),
):
    leave_types = db.query(LeaveType).order_by(LeaveType.name).all()
    rules_by_leave_type_id = {
        rule.leave_type_id: rule for rule in db.query(ApprovalRoutingRule).all()
    }

    return [
        _serialize(leave_type, rules_by_leave_type_id.get(leave_type.id))
        for leave_type in leave_types
    ]


@router.put("/{leave_type_id}", response_model=ApprovalRoutingRuleRead)
def update_approval_routing(
    leave_type_id: int,
    payload: ApprovalRoutingRuleUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(["ADMIN"])),
):
    leave_type = db.query(LeaveType).filter(LeaveType.id == leave_type_id).first()
    if leave_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave type not found.")

    rule = (
        db.query(ApprovalRoutingRule)
        .filter(ApprovalRoutingRule.leave_type_id == leave_type_id)
        .first()
    )

    chain_value = ",".join(payload.approval_chain)
    if rule is None:
        rule = ApprovalRoutingRule(leave_type_id=leave_type_id, approval_chain=chain_value)
        db.add(rule)
    else:
        rule.approval_chain = chain_value

    db.commit()
    db.refresh(rule)

    return _serialize(leave_type, rule)
