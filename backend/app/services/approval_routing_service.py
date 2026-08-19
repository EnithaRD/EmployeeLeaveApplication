from app.models.approval_routing_rule import ApprovalRoutingRule
from app.models.leave_type import LeaveType

DEFAULT_CHAINS_BY_LEAVE_TYPE_NAME = {
    "long leave": ["HR"],
    "sick leave": ["MANAGER"],
    "casual leave": ["MANAGER"],
    "emergency leave": ["MANAGER", "HR"],
}

FALLBACK_CHAIN = ["MANAGER"]


def default_chain_for_name(leave_type_name: str) -> list[str]:
    normalized = (leave_type_name or "").strip().lower()
    return list(DEFAULT_CHAINS_BY_LEAVE_TYPE_NAME.get(normalized, FALLBACK_CHAIN))


def seed_default_routing_rules(db) -> None:
    leave_types = db.query(LeaveType).all()
    existing_leave_type_ids = {
        rule.leave_type_id for rule in db.query(ApprovalRoutingRule).all()
    }

    for leave_type in leave_types:
        if leave_type.id in existing_leave_type_ids:
            continue

        chain = default_chain_for_name(leave_type.name)
        db.add(
            ApprovalRoutingRule(
                leave_type_id=leave_type.id,
                approval_chain=",".join(chain),
            )
        )

    db.commit()


def get_chain_for_leave_type(db, leave_type: LeaveType) -> list[str]:
    rule = (
        db.query(ApprovalRoutingRule)
        .filter(ApprovalRoutingRule.leave_type_id == leave_type.id)
        .first()
    )
    if rule is not None:
        return rule.approval_chain.split(",")

    return default_chain_for_name(leave_type.name)
