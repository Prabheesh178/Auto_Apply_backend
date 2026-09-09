from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

class CandidateBase(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    raw_resume_text: Optional[str] = ""
    structured_profile: Optional[Dict[str, Any]] = {}

class CandidateCreate(CandidateBase):
    pass

class CandidateUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    structured_profile: Optional[Dict[str, Any]] = None

class CandidateResponse(CandidateBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
