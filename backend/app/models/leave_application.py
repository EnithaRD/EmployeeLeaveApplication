from sqlalchemy import Column, Integer, ForeignKey, String, Date, Numeric, Text, DateTime, func
from app.db.base import Base


class LeaveApplication(Base):
    __tablename__ = "leave_applications"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_count = Column(Numeric(4, 1), nullable=False)
    reason = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, server_default="PENDING")
    approver_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    approver_comment = Column(String(500), nullable=True)
    applied_at = Column(DateTime, nullable=False, server_default=func.now())
    decided_at = Column(DateTime, nullable=True)
