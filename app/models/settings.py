from datetime import datetime
from sqlalchemy import Column, Integer, Boolean, JSON, DateTime
from app.database import Base

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, default=1)
    review_before_submit = Column(Boolean, nullable=False, default=True)
    is_agent_paused = Column(Boolean, nullable=False, default=False)
    target_roles = Column(JSON, nullable=False, default=lambda: [
        "Software Engineer Intern",
        "Full Stack Intern",
        "Backend Intern",
        "Frontend Intern",
        "AI/ML Intern",
        "Data Science Intern"
    ])
    target_locations = Column(JSON, nullable=False, default=lambda: ["Remote", "United States", "India", "Hybrid"])
    min_match_score = Column(Integer, nullable=False, default=70)
    max_daily_applications = Column(Integer, nullable=False, default=15)
    monitored_companies = Column(JSON, nullable=False, default=lambda: [
        {"name": "Stripe", "ats": "greenhouse", "slug": "stripe"},
        {"name": "Figma", "ats": "greenhouse", "slug": "figma"},
        {"name": "Airbnb", "ats": "greenhouse", "slug": "airbnb"},
        {"name": "Coinbase", "ats": "greenhouse", "slug": "coinbase"},
        {"name": "Scale AI", "ats": "greenhouse", "slug": "scaleai"},
        {"name": "Ramp", "ats": "ashby", "slug": "ramp"},
        {"name": "Notion", "ats": "lever", "slug": "notion"},
        {"name": "Vercel", "ats": "ashby", "slug": "vercel"}
    ])
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
