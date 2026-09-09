import os
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.application import Application
from app.models.job import JobListing
from app.schemas.application import ApplicationResponse, ApplicationCustomize
from app.modules.generation.materials_pipeline import materials_pipeline
from app.modules.automation.orchestrator import automation_orchestrator
from app.services.activity_service import activity_service

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get("", response_model=List[ApplicationResponse])
async def get_applications(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Application)
        .join(Application.job)
        .options(selectinload(Application.job))
        .order_by(desc(Application.updated_at))
    )

    if status and status != "all":
        query = query.where(Application.status == status)

    if platform and platform != "all":
        query = query.where(JobListing.ats_platform == platform)

    if search:
        search_fmt = f"%{search}%"
        query = query.where(
            (JobListing.company_name.ilike(search_fmt)) |
            (JobListing.role_title.ilike(search_fmt))
        )

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(app_id: str, db: AsyncSession = Depends(get_db)):
    query = (
        select(Application)
        .where(Application.id == app_id)
        .options(selectinload(Application.job))
    )
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

@router.post("/{app_id}/generate-materials")
async def generate_application_materials(app_id: str):
    """Generates tailored cover letter, resume bullets, ATS PDF, and form answers."""
    result = await materials_pipeline.prepare_application_materials(app_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/{app_id}/resume-pdf")
async def get_application_resume_pdf(app_id: str, db: AsyncSession = Depends(get_db)):
    """Serves the generated ATS-optimized PDF resume for preview and download."""
    query = select(Application).where(Application.id == app_id)
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    pdf_path = app.tailored_resume_pdf_path
    if not pdf_path or not os.path.exists(pdf_path):
        gen_res = await materials_pipeline.prepare_application_materials(app_id)
        pdf_path = gen_res.get("pdf_path")
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="Resume PDF not available yet")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"Resume_{app.job.company_name if app.job else 'Tailored'}.pdf"
    )

@router.get("/{app_id}/screenshot")
async def get_application_screenshot(app_id: str, db: AsyncSession = Depends(get_db)):
    """Serves the captured submission proof screenshot."""
    query = select(Application).where(Application.id == app_id)
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app or not app.submission_screenshot_path or not os.path.exists(app.submission_screenshot_path):
        raise HTTPException(status_code=404, detail="Submission screenshot not found")

    return FileResponse(app.submission_screenshot_path, media_type="image/png")

@router.post("/{app_id}/prefill")
async def prefill_application_endpoint(
    app_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Automates fill only: populates form, attaches PDF, captures pre-fill screenshot, and stops for review.
    """
    query = (
        select(Application)
        .where(Application.id == app_id)
        .options(selectinload(Application.job))
    )
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    background_tasks.add_task(automation_orchestrator.prefill_application, application_id=app.id)
    return {"message": "Form pre-fill started in background", "status": "prefilling"}

@router.post("/{app_id}/approve")
async def approve_application(
    app_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Candidate explicitly approves application -> launches final submission in background.
    """
    query = (
        select(Application)
        .where(Application.id == app_id)
        .options(selectinload(Application.job))
    )
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = "approved"
    app.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(app)

    company = app.job.company_name if app.job else "Company"
    role = app.job.role_title if app.job else "Role"
    await activity_service.log(
        "SUCCESS",
        "ReviewQueue",
        f"Application for {company} ({role}) explicitly approved. Executing final submission...",
        {"application_id": app.id}
    )

    # Trigger Playwright final submit in background
    background_tasks.add_task(automation_orchestrator.execute_final_submission, application_id=app.id)

    return {"message": "Application approved and executing final submission", "status": "approved"}

@router.put("/{app_id}/customize", response_model=ApplicationResponse)
async def customize_application(
    app_id: str,
    customize_data: ApplicationCustomize,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Application)
        .where(Application.id == app_id)
        .options(selectinload(Application.job))
    )
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if customize_data.cover_letter_text is not None:
        app.cover_letter_text = customize_data.cover_letter_text
    if customize_data.form_answers is not None:
        app.form_answers = customize_data.form_answers
    if customize_data.tailored_resume_json is not None:
        app.tailored_resume_json = customize_data.tailored_resume_json

    app.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(app)

    company = app.job.company_name if app.job else "Company"
    await activity_service.log(
        "INFO",
        "Tailorer",
        f"Application materials customized for {company}.",
        {"application_id": app.id}
    )

    return app

@router.post("/{app_id}/reject")
async def reject_application(app_id: str, db: AsyncSession = Depends(get_db)):
    query = (
        select(Application)
        .where(Application.id == app_id)
        .options(selectinload(Application.job))
    )
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = "rejected"
    app.updated_at = datetime.utcnow()
    await db.commit()

    company = app.job.company_name if app.job else "Company"
    await activity_service.log("INFO", "ReviewQueue", f"Application for {company} dismissed by candidate.")

    return {"message": "Application dismissed", "status": "rejected"}

@router.post("/{app_id}/retry")
async def retry_application(
    app_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Application)
        .where(Application.id == app_id)
        .options(selectinload(Application.job))
    )
    result = await db.execute(query)
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = "pending_review"
    app.submission_error = None
    app.updated_at = datetime.utcnow()
    await db.commit()

    company = app.job.company_name if app.job else "Company"
    await activity_service.log("INFO", "ReviewQueue", f"Retrying submission for {company}.")

    return {"message": "Application requeued for review", "status": "pending_review"}
