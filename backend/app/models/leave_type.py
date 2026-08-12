from sqlalchemy import Column, Integer, String
from app.db.base import Base


class LeaveType(Base):
    __tablename__ = "leave_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    default_annual_quota = Column(Integer, nullable=False, default=0)
    description = Column(String(255), nullable=True)
