from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.database import get_db
from app.models.email_log import EmailLog
from app.models.application import Application
from app.modules.watcher.gmail_client import gmail_client
from app.modules.watcher.sync import watcher_sync_service

router = APIRouter(prefix="/watcher", tags=["Watcher"])

class SimulateEmailRequest(BaseModel):
    sender: str
    subject: str
    snippet: str
    body_text: Optional[str] = None
    company_name: Optional[str] = None

@router.get("/status")
async def get_watcher_status(db: AsyncSession = Depends(get_db)):
    """Returns Gmail client connection status and sync stats."""
    count_res = await db.execute(select(func.count(EmailLog.id)))
    total_emails = count_res.scalar_one() or 0

    latest_res = await db.execute(select(EmailLog).order_by(desc(EmailLog.created_at)).limit(1))
    latest_log = latest_res.scalar_one_or_none()

    return {
        "gmail_connected": gmail_client.is_connected(),
        "total_emails_processed": total_emails,
        "last_sync_at": latest_log.created_at.isoformat() if latest_log else None
    }

@router.post("/sync")
async def trigger_email_sync(background_tasks: BackgroundTasks):
    """Triggers a background sync of recent recruiter emails from Gmail."""
    background_tasks.add_task(watcher_sync_service.sync_all_recent_emails)
    return {"message": "Gmail reply sync initiated in background", "status": "running"}

@router.get("/logs")
async def get_email_logs(
    category: Optional[str] = None,
    limit: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Returns processed recruiter email logs with classification details."""
    query = select(EmailLog).order_by(desc(EmailLog.received_at))
    if category and category != "all":
        query = query.where(EmailLog.category == category)
    query = query.limit(limit)
    res = await db.execute(query)
    logs = res.scalars().all()

    return [
        {
            "id": l.id,
            "application_id": l.application_id,
            "sender": l.sender,
            "subject": l.subject,
            "snippet": l.snippet,
            "category": l.category,
            "confidence_score": l.confidence_score,
            "received_at": l.received_at.isoformat()
        }
        for l in logs
    ]

@router.post("/simulate-email")
async def simulate_incoming_email(payload: SimulateEmailRequest):
    """Simulates an incoming recruiter email to test Gemini intent classification and tracker updates."""
    email_data = {
        "sender": payload.sender,
        "subject": payload.subject,
        "snippet": payload.snippet,
        "body_text": payload.body_text or payload.snippet,
        "received_at": datetime.utcnow()
    }
    result = await watcher_sync_service.process_incoming_email(email_data)
    return result
