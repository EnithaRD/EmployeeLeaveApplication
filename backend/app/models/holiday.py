from sqlalchemy import Column, Integer, String, Date
from app.db.base import Base


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    holiday_date = Column(Date, nullable=False, unique=True)
