import asyncio
import uuid
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.settings import SystemSettings
from app.models.candidate import Candidate
from app.models.job import JobListing
from app.models.application import Application
from app.modules.discovery.greenhouse import greenhouse_client
from app.modules.discovery.lever import lever_client
from app.modules.discovery.ashby import ashby_client
from app.modules.discovery.smartrecruiters import smartrecruiters_client
from app.modules.matching.matcher import semantic_matcher
from app.services.activity_service import activity_service

class DiscoveryOrchestrator:
    async def fetch_from_platform(self, platform: str, company_slug: str) -> List[Dict[str, Any]]:
        """Dispatch fetch to corresponding ATS client."""
        platform = platform.lower()
        if platform == "greenhouse":
            return await greenhouse_client.fetch_company_jobs(company_slug)
        elif platform == "lever":
            return await lever_client.fetch_company_jobs(company_slug)
        elif platform == "ashby":
            return await ashby_client.fetch_company_jobs(company_slug)
        elif platform == "smartrecruiters":
            return await smartrecruiters_client.fetch_company_jobs(company_slug)
        return []

    async def run_discovery_sweep(self) -> Dict[str, Any]:
        """
        Runs a full job discovery sweep across all configured companies and ATS platforms.
        Scores discovered jobs with Gemini and creates tracker entries.
        """
        async with AsyncSessionLocal() as session:
            # 1. Fetch settings & candidate profile
            settings_res = await session.execute(select(SystemSettings).where(SystemSettings.id == 1))
            settings = settings_res.scalar_one_or_none()
            if not settings:
                return {"error": "System settings not found"}

            if settings.is_agent_paused:
                await activity_service.log("WARN", "Discovery", "Discovery sweep skipped: Agent is currently PAUSED.")
                return {"status": "paused", "message": "Agent is paused"}

            candidate_res = await session.execute(select(Candidate))
            candidate = candidate_res.scalars().first()
            candidate_profile = candidate.structured_profile if candidate else {}

            monitored = settings.monitored_companies or []
            target_roles = [r.lower() for r in (settings.target_roles or [])]
            min_score = settings.min_match_score or 70

            await activity_service.log(
                "INFO",
                "Discovery",
                f"Starting ATS sweep across {len(monitored)} companies (Targeting: {', '.join(settings.target_roles[:3])})..."
            )

            # 2. Concurrently fetch jobs from all platforms
            tasks = []
            for comp in monitored:
                slug = comp.get("slug")
                ats = comp.get("ats", "greenhouse")
                if slug:
                    tasks.append(self.fetch_from_platform(ats, slug))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_raw_jobs: List[Dict[str, Any]] = []
            for res in results:
                if isinstance(res, list):
                    all_raw_jobs.extend(res)

            await activity_service.log(
                "INFO", 
                "Discovery", 
                f"Scanned {len(all_raw_jobs)} total live postings from ATS endpoints."
            )

            # 3. Filter relevant roles (internships or matching target roles)
            relevant_jobs = []
            for job in all_raw_jobs:
                title_lower = job.get("role_title", "").lower()
                is_role_match = not target_roles or any(
                    role_kw in title_lower for role_kw in [
                        "intern", "internship", "co-op", "coop", "software", "engineer", "developer", 
                        "frontend", "backend", "full stack", "fullstack", "ai", "ml", "data", "systems"
                    ]
                )
                if is_role_match:
                    relevant_jobs.append(job)

            # 4. Check existing URLs in DB to prevent duplicates
            existing_urls_res = await session.execute(select(JobListing.job_url))
            existing_urls = set(existing_urls_res.scalars().all())

            new_jobs_count = 0
            high_matches_count = 0

            for job_data in relevant_jobs:
                job_url = job_data.get("job_url")
                if not job_url or job_url in existing_urls:
                    continue

                existing_urls.add(job_url)
                new_jobs_count += 1

                # 5. Evaluate Match with Gemini
                evaluation = await semantic_matcher.evaluate_match(candidate_profile, job_data)
                match_score = evaluation.get("match_score", 70)
                match_rationale = evaluation.get("match_rationale", "")

                job_id = str(uuid.uuid4())
                job_listing = JobListing(
                    id=job_id,
                    company_name=job_data.get("company_name", "Company"),
                    role_title=job_data.get("role_title", "Role"),
                    location=job_data.get("location", "Remote"),
                    ats_platform=job_data.get("ats_platform", "direct"),
                    job_url=job_url,
                    ats_job_id=job_data.get("ats_job_id"),
                    job_description=job_data.get("job_description", ""),
                    requirements=job_data.get("requirements", []),
                    is_internship=job_data.get("is_internship", True),
                    match_score=match_score,
                    match_rationale=match_rationale,
                    discovered_at=datetime.utcnow()
                )
                session.add(job_listing)

                # 6. If high match, queue in application tracker
                if match_score >= min_score:
                    high_matches_count += 1
                    app_id = str(uuid.uuid4())
                    app = Application(
                        id=app_id,
                        job_id=job_id,
                        candidate_id=candidate.id if candidate else None,
                        status="pending_review",
                        form_answers={
                            "authorized_us": "Yes",
                            "requires_sponsorship": "No",
                            "graduation_date": candidate_profile.get("education", [{}])[0].get("graduation_date", "2026")
                        }
                    )
                    session.add(app)
                    await activity_service.log(
                        "SUCCESS",
                        "Discovery",
                        f"High-match found: {job_listing.company_name} - {job_listing.role_title} ({match_score}% fit). Queued in Review Queue.",
                        {"job_id": job_id, "score": match_score}
                    )
                else:
                    await activity_service.log(
                        "INFO",
                        "Matcher",
                        f"Evaluated {job_listing.company_name} ({job_listing.role_title}) -> {match_score}% fit."
                    )

            await session.commit()

            summary_msg = (
                f"Discovery sweep finished: {len(all_raw_jobs)} scanned, {new_jobs_count} new postings evaluated, "
                f"{high_matches_count} high-match roles queued for review."
            )
            await activity_service.log("SUCCESS", "Discovery", summary_msg)

            return {
                "status": "success",
                "scanned_count": len(all_raw_jobs),
                "new_jobs_count": new_jobs_count,
                "high_matches_count": high_matches_count
            }

discovery_orchestrator = DiscoveryOrchestrator()
