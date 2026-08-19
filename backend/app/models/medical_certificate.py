from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from app.db.base import Base


class MedicalCertificate(Base):
    __tablename__ = "medical_certificates"

    id = Column(Integer, primary_key=True, index=True)
    leave_application_id = Column(
        Integer,
        ForeignKey("leave_applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, nullable=False, server_default=func.now())
