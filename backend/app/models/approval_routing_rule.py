from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from app.db.base import Base


class ApprovalRoutingRule(Base):
    __tablename__ = "approval_routing_rules"

    id = Column(Integer, primary_key=True, index=True)
    leave_type_id = Column(
        Integer,
        ForeignKey("leave_types.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    approval_chain = Column(String(100), nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
