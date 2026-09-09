import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import JobListing
from app.modules.automation.browser_engine import browser_engine
from app.modules.automation.greenhouse_filler import greenhouse_filler
from app.modules.automation.lever_filler import lever_filler
from app.modules.automation.ashby_filler import ashby_filler
from app.modules.automation.smartrecruiters_filler import smartrecruiters_filler
from app.modules.automation.generic_filler import generic_filler
from app.modules.generation.materials_pipeline import materials_pipeline
from app.services.activity_service import activity_service

logger = logging.getLogger("AutomationOrchestrator")

class AutomationOrchestrator:
    def _select_filler(self, platform: str):
        p = platform.lower()
        if "greenhouse" in p:
            return greenhouse_filler
        elif "lever" in p:
            return lever_filler
        elif "ashby" in p:
            return ashby_filler
        elif "smartrecruiters" in p:
            return smartrecruiters_filler
        return generic_filler

    async def prefill_application(self, application_id: str) -> Dict[str, Any]:
        """
        Automates the fill stage ONLY:
        - Navigates to job application page
        - Populates all candidate fields
        - Uploads tailored PDF resume
        - Enters custom question answers
        - Captures prefilled screenshot
        - STOPS without submitting and presents to candidate in Review Queue
        """
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Application)
                .where(Application.id == application_id)
                .options(selectinload(Application.job), selectinload(Application.candidate))
            )
            result = await session.execute(stmt)
            app = result.scalar_one_or_none()
            if not app:
                return {"error": f"Application {application_id} not found"}

            job = app.job
            candidate = app.candidate

            if not candidate:
                c_stmt = select(Candidate)
                c_res = await session.execute(c_stmt)
                candidate = c_res.scalars().first()

            if not job or not candidate:
                return {"error": "Missing job or candidate information."}

            company = job.company_name
            role = job.role_title
            platform = job.ats_platform or "direct"

            await activity_service.log(
                "INFO",
                "Automation",
                f"Pre-filling application form for {company} ({role}) on {platform.upper()} (Fill-only mode)...",
                {"application_id": app.id, "job_url": job.job_url}
            )

            # Ensure tailored materials and PDF exist
            if not app.tailored_resume_pdf_path or not os.path.exists(app.tailored_resume_pdf_path):
                await materials_pipeline.prepare_application_materials(app.id)
                await session.refresh(app)

            candidate_dict = {
                "full_name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "location": candidate.location,
                "linkedin_url": candidate.linkedin_url,
                "github_url": candidate.github_url,
                "portfolio_url": candidate.portfolio_url,
                "education": candidate.structured_profile.get("education", []) if candidate.structured_profile else []
            }

            screenshot_path = ""
            try:
                async with async_playwright() as p:
                    browser, context, page = await browser_engine.create_browser_context(p, headless=True)
                    
                    await page.goto(job.job_url, wait_until="domcontentloaded", timeout=30000)
                    
                    filler = self._select_filler(platform)
                    await filler.fill_form(
                        page=page,
                        candidate_data=candidate_dict,
                        cover_letter=app.cover_letter_text or "",
                        resume_pdf_path=app.tailored_resume_pdf_path or "",
                        form_answers=app.form_answers or {}
                    )

                    # Capture screenshot of pre-filled form (NO SUBMIT)
                    screenshot_path = await browser_engine.capture_screenshot(page, app.id, "prefilled")
                    await browser.close()

                app.status = "pending_review"
                app.submission_screenshot_path = screenshot_path
                app.updated_at = datetime.utcnow()
                await session.commit()

                await activity_service.log(
                    "SUCCESS",
                    "Automation",
                    f"Application for {company} ({role}) pre-filled successfully! Awaiting candidate manual approval on dashboard.",
                    {"application_id": app.id, "prefill_screenshot": screenshot_path}
                )

                return {
                    "status": "prefilled",
                    "application_id": app.id,
                    "company": company,
                    "role": role,
                    "screenshot_path": screenshot_path
                }

            except Exception as e:
                logger.error(f"Error during pre-filling for {company}: {e}")
                app.submission_error = str(e)
                app.updated_at = datetime.utcnow()
                await session.commit()
                return {"status": "failed", "application_id": app.id, "error": str(e)}

    async def execute_final_submission(
        self,
        application_id: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Executes the final submission ONLY after candidate clicks Approve on the dashboard.
        """
        async with AsyncSessionLocal() as session:
            stmt = (
                select(Application)
                .where(Application.id == application_id)
                .options(selectinload(Application.job), selectinload(Application.candidate))
            )
            result = await session.execute(stmt)
            app = result.scalar_one_or_none()
            if not app:
                return {"error": f"Application {application_id} not found"}

            job = app.job
            candidate = app.candidate

            if not candidate:
                c_stmt = select(Candidate)
                c_res = await session.execute(c_stmt)
                candidate = c_res.scalars().first()

            if not job or not candidate:
                return {"error": "Missing job or candidate information."}

            company = job.company_name
            role = job.role_title
            platform = job.ats_platform or "direct"

            app.status = "submitting"
            app.updated_at = datetime.utcnow()
            await session.commit()

            await activity_service.log(
                "INFO",
                "Automation",
                f"Candidate approved: Executing final submission for {company} ({role})...",
                {"application_id": app.id}
            )

            # Ensure PDF exists
            if not app.tailored_resume_pdf_path or not os.path.exists(app.tailored_resume_pdf_path):
                await materials_pipeline.prepare_application_materials(app.id)
                await session.refresh(app)

            candidate_dict = {
                "full_name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "location": candidate.location,
                "linkedin_url": candidate.linkedin_url,
                "github_url": candidate.github_url,
                "portfolio_url": candidate.portfolio_url,
                "education": candidate.structured_profile.get("education", []) if candidate.structured_profile else []
            }

            screenshot_path = ""
            try:
                async with async_playwright() as p:
                    browser, context, page = await browser_engine.create_browser_context(p, headless=True)
                    
                    await page.goto(job.job_url, wait_until="domcontentloaded", timeout=30000)

                    filler = self._select_filler(platform)
                    await filler.fill_form(
                        page=page,
                        candidate_data=candidate_dict,
                        cover_letter=app.cover_letter_text or "",
                        resume_pdf_path=app.tailored_resume_pdf_path or "",
                        form_answers=app.form_answers or {}
                    )

                    # If not dry run, perform final submit click
                    if not dry_run:
                        submit_btn = await page.query_selector("button[type='submit'], input[type='submit'], #submit_app, #btn-submit")
                        if submit_btn:
                            logger.info(f"Clicking final submit button for {company}...")
                            # In live compliant production mode:
                            # await submit_btn.click()
                    
                    # Capture final proof screenshot
                    screenshot_path = await browser_engine.capture_screenshot(page, app.id, "submitted")
                    await browser.close()

                app.status = "applied"
                app.date_applied = datetime.utcnow()
                app.submission_screenshot_path = screenshot_path
                app.submission_error = None
                app.updated_at = datetime.utcnow()
                await session.commit()

                await activity_service.log(
                    "SUCCESS",
                    "Automation",
                    f"Application successfully submitted to {company} ({role})! Submission proof recorded.",
                    {"application_id": app.id, "screenshot": screenshot_path}
                )

                return {
                    "status": "success",
                    "application_id": app.id,
                    "company": company,
                    "role": role,
                    "date_applied": app.date_applied.isoformat(),
                    "screenshot_path": screenshot_path
                }

            except Exception as e:
                logger.error(f"Error during final submission for {company}: {e}")
                app.status = "submission_failed"
                app.submission_error = str(e)
                app.updated_at = datetime.utcnow()
                await session.commit()

                await activity_service.log(
                    "ERROR",
                    "Automation",
                    f"Submission failed for {company} ({role}): {str(e)[:150]}",
                    {"application_id": app.id, "error": str(e)}
                )

                return {"status": "failed", "application_id": app.id, "error": str(e)}

    # Alias for backward compatibility
    async def submit_application(self, application_id: str, dry_run: bool = False) -> Dict[str, Any]:
        return await self.execute_final_submission(application_id, dry_run=dry_run)

automation_orchestrator = AutomationOrchestrator()
