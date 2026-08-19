from datetime import datetime
from pydantic import BaseModel


class MedicalCertificateRead(BaseModel):
    id: int
    leave_application_id: int
    original_filename: str
    content_type: str
    file_size: int
    uploaded_at: datetime

    model_config = {
        "from_attributes": True,
    }
