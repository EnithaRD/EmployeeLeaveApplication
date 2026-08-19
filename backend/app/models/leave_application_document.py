from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String, func
from app.db.base import Base


class LeaveApplicationDocument(Base):
    __tablename__ = "leave_application_documents"

    id = Column(Integer, primary_key=True, index=True)
    leave_application_id = Column(
        Integer,
        ForeignKey("leave_applications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_data = Column(LargeBinary, nullable=False)
    uploaded_at = Column(DateTime, nullable=False, server_default=func.now())
