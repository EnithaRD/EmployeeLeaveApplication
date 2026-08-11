from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.base import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), nullable=False, unique=True)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
