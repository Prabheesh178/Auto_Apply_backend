import asyncio
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.job import JobListing
from app.schemas.job import JobResponse
from app.modules.discovery.orchestrator import discovery_orchestrator
from app.services.activity_service import activity_service

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("", response_model=List[JobResponse])
async def get_jobs(
    platform: Optional[str] = None,
    min_score: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(JobListing).order_by(desc(JobListing.match_score))

    if platform and platform != "all":
        query = query.where(JobListing.ats_platform == platform)

    if min_score is not None:
        query = query.where(JobListing.match_score >= min_score)

    if search:
        search_fmt = f"%{search}%"
        query = query.where(
            (JobListing.company_name.ilike(search_fmt)) |
            (JobListing.role_title.ilike(search_fmt)) |
            (JobListing.location.ilike(search_fmt))
        )

    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/trigger-discovery")
async def trigger_discovery(background_tasks: BackgroundTasks):
    """Trigger an autonomous job discovery sweep across Greenhouse, Lever, Ashby, and SmartRecruiters."""
    # Launch in background so client receives fast response while SSE logs progress
    background_tasks.add_task(discovery_orchestrator.run_discovery_sweep)
    
    return {
        "message": "Job discovery sweep initiated across ATS platforms",
        "status": "running"
    }
