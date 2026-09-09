import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models.application import Application
from app.models.candidate import Candidate
from app.modules.generation.cover_letter import cover_letter_generator
from app.modules.generation.resume_tailor import resume_tailorer
from app.modules.generation.question_answerer import question_answerer
from app.modules.generation.pdf_generator import resume_pdf_generator
from app.services.activity_service import activity_service

class MaterialsPipeline:
    async def prepare_application_materials(
        self,
        application_id: str,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end tailored generation for an application:
        1. Generates targeted cover letter with Gemini
        2. Tailors resume bullet points and re-orders technical skills
        3. Pre-fills ATS form questions
        4. Compiles pristine ATS-friendly single-page PDF
        5. Updates application in database
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

            # If application doesn't have a linked candidate, grab default
            if not candidate:
                c_stmt = select(Candidate)
                c_res = await session.execute(c_stmt)
                candidate = c_res.scalars().first()

            if not candidate:
                return {"error": "No candidate profile available to generate materials."}

            candidate_dict = {
                "full_name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "location": candidate.location,
                "linkedin_url": candidate.linkedin_url,
                "github_url": candidate.github_url,
                "portfolio_url": candidate.portfolio_url,
                "structured_profile": candidate.structured_profile or {}
            }

            job_dict = {
                "company_name": job.company_name if job else "Company",
                "role_title": job.role_title if job else "Role",
                "location": job.location if job else "Remote",
                "job_description": job.job_description if job else "",
                "ats_platform": job.ats_platform if job else "direct"
            }

            company = job_dict["company_name"]
            role = job_dict["role_title"]

            await activity_service.log(
                "INFO",
                "Tailorer",
                f"Generating customized application materials for {company} ({role})...",
                {"application_id": app.id}
            )

            # 1. Generate Cover Letter
            cover_letter = await cover_letter_generator.generate_cover_letter(
                candidate_profile=candidate_dict["structured_profile"],
                job_data=job_dict,
                match_rationale=job.match_rationale if job else None
            )

            # 2. Tailor Resume Bullets & Re-order Skills
            tailored_resume = await resume_tailorer.tailor_resume(
                candidate_profile=candidate_dict["structured_profile"],
                job_data=job_dict
            )

            # 3. Generate Answers for ATS Questions
            form_answers = await question_answerer.generate_answers(
                candidate_profile=candidate_dict["structured_profile"],
                job_data=job_dict
            )

            # 4. Compile Single-Page ATS PDF
            pdf_path = await resume_pdf_generator.generate_pdf(
                application_id=app.id,
                candidate=candidate_dict,
                tailored_data=tailored_resume
            )

            # 5. Persist to Database
            app.cover_letter_text = cover_letter
            app.tailored_resume_json = tailored_resume
            app.tailored_resume_pdf_path = pdf_path
            app.form_answers = form_answers
            app.updated_at = datetime.utcnow()

            await session.commit()

            await activity_service.log(
                "SUCCESS",
                "Tailorer",
                f"Completed application materials for {company}: Cover letter, tailored resume PDF, and form answers ready.",
                {"application_id": app.id, "pdf_path": pdf_path}
            )

            flagged = form_answers.get("flagged_fields", [])
            if flagged:
                await activity_service.log(
                    "WARNING",
                    "Tailorer",
                    f"{len(flagged)} field(s) flagged for manual candidate input for {company}.",
                    {"application_id": app.id, "flagged": [f.get('field') for f in flagged]}
                )

            return {
                "status": "success",
                "application_id": app.id,
                "company": company,
                "role": role,
                "cover_letter_preview": cover_letter[:200] + "...",
                "pdf_path": pdf_path,
                "tailored_skills": tailored_resume.get("skills", {}),
                "form_answers": form_answers
            }

materials_pipeline = MaterialsPipeline()
