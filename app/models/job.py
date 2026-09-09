import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Integer
from app.database import Base

class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(255), nullable=False)
    role_title = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    ats_platform = Column(String(50), nullable=False) # greenhouse, lever, ashby, smartrecruiters, direct
    job_url = Column(Text, nullable=False, unique=True)
    ats_job_id = Column(String(255), nullable=True)
    job_description = Column(Text, nullable=False)
    requirements = Column(JSON, nullable=False, default=list)
    is_internship = Column(Boolean, default=True)
    match_score = Column(Integer, nullable=True) # 0 to 100
    match_rationale = Column(Text, nullable=True)
    discovered_at = Column(DateTime, default=datetime.utcnow)
