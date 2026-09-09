from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.application import Application
from app.models.job import JobListing
from app.models.activity_log import ActivityLog
from app.schemas.analytics import AnalyticsSummary

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    # Total jobs discovered
    jobs_count_res = await db.execute(select(func.count(JobListing.id)))
    total_discovered = jobs_count_res.scalar_one() or 0

    # Applications status breakdown
    status_res = await db.execute(
        select(Application.status, func.count(Application.id)).group_by(Application.status)
    )
    status_dict = {row[0]: row[1] for row in status_res.all()}

    total_applied = status_dict.get("applied", 0) + status_dict.get("interview", 0) + status_dict.get("rejected", 0)
    pending_review = status_dict.get("pending_review", 0)
    interviews = status_dict.get("interview", 0)
    rejections = status_dict.get("rejected", 0)
    no_response = status_dict.get("applied", 0)

    conversion_rate = round((interviews / max(total_applied, 1)) * 100, 1)

    # Platform breakdown
    platform_res = await db.execute(
        select(JobListing.ats_platform, func.count(JobListing.id)).group_by(JobListing.ats_platform)
    )
    platform_breakdown = {row[0]: row[1] for row in platform_res.all()}

    # Recent activity
    logs_res = await db.execute(
        select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(10)
    )
    recent_logs = [
        {
            "id": log.id,
            "level": log.level,
            "component": log.component,
            "message": log.message,
            "created_at": log.created_at.isoformat()
        }
        for log in logs_res.scalars().all()
    ]

    return AnalyticsSummary(
        total_discovered=total_discovered,
        total_applied=total_applied,
        pending_review=pending_review,
        interviews=interviews,
        rejections=rejections,
        no_response=no_response,
        conversion_rate=conversion_rate,
        platform_breakdown=platform_breakdown,
        recent_activity=recent_logs
    )
