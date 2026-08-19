from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from app.db.base import Base


class LeaveApplicationStep(Base):
    __tablename__ = "leave_application_steps"

    id = Column(Integer, primary_key=True, index=True)
    leave_application_id = Column(Integer, ForeignKey("leave_applications.id", ondelete="CASCADE"), nullable=False)
    step_order = Column(Integer, nullable=False)
    approver_role = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="WAITING")
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    comment = Column(String(500), nullable=True)
    decided_at = Column(DateTime, nullable=True)
