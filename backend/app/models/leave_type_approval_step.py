from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from app.db.base import Base


class LeaveTypeApprovalStep(Base):
    __tablename__ = "leave_type_approval_steps"
    __table_args__ = (
        UniqueConstraint("leave_type_id", "step_order", name="uq_leave_type_step_order"),
    )

    id = Column(Integer, primary_key=True, index=True)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id", ondelete="CASCADE"), nullable=False)
    step_order = Column(Integer, nullable=False)
    approver_role = Column(String(20), nullable=False)
