import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Float, ForeignKey
from app.database import Base

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    message_id = Column(String(255), nullable=False, unique=True)
    thread_id = Column(String(255), nullable=True)
    sender = Column(String(255), nullable=False)
    subject = Column(Text, nullable=False)
    snippet = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=False)
    category = Column(String(50), nullable=False, default="general") # ack, rejection, interview_invite, assessment, general
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
