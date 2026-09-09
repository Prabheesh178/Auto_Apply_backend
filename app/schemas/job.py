from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class JobBase(BaseModel):
    company_name: str
    role_title: str
    location: Optional[str] = None
    ats_platform: str
    job_url: str
    ats_job_id: Optional[str] = None
    job_description: str
    requirements: Optional[List[Any]] = []
    is_internship: Optional[bool] = True
    match_score: Optional[int] = None
    match_rationale: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: str
    discovered_at: datetime

    class Config:
        from_attributes = True
