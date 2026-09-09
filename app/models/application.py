import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("job_listings.id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=True)
    status = Column(String(50), nullable=False, default="discovered") # discovered, pending_review, approved, submitting, applied, failed, replied, interview, rejected
    cover_letter_text = Column(Text, nullable=True)
    tailored_resume_pdf_path = Column(Text, nullable=True)
    tailored_resume_json = Column(JSON, nullable=True)
    form_answers = Column(JSON, nullable=False, default=dict)
    submission_screenshot_path = Column(Text, nullable=True)
    submission_error = Column(Text, nullable=True)
    date_applied = Column(DateTime, nullable=True)
    last_reply_snippet = Column(Text, nullable=True)
    last_reply_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("JobListing", backref="applications", lazy="joined")
    candidate = relationship("Candidate", backref="applications", lazy="joined")
