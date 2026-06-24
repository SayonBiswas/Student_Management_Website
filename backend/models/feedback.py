from pydantic import BaseModel
from typing import Optional

class FeedbackCreate(BaseModel):
    admission_number: int
    subject_name: Optional[str] = None
    feedback_text: str
    role: str = "teacher"