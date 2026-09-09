from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.schemas.job import JobResponse

class ApplicationBase(BaseModel):
    job_id: str
    candidate_id: Optional[str] = None
    status: str = "discovered"
    cover_letter_text: Optional[str] = None
    tailored_resume_pdf_path: Optional[str] = None
    tailored_resume_json: Optional[Dict[str, Any]] = None
    form_answers: Optional[Dict[str, Any]] = {}
    submission_screenshot_path: Optional[str] = None
    submission_error: Optional[str] = None
    date_applied: Optional[datetime] = None
    last_reply_snippet: Optional[str] = None
    last_reply_at: Optional[datetime] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationCustomize(BaseModel):
    cover_letter_text: Optional[str] = None
    form_answers: Optional[Dict[str, Any]] = None
    tailored_resume_json: Optional[Dict[str, Any]] = None

class ApplicationResponse(ApplicationBase):
    id: str
    created_at: datetime
    updated_at: datetime
    job: Optional[JobResponse] = None

    class Config:
        from_attributes = True
