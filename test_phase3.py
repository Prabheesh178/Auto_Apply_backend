import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.candidate import Candidate
from app.models.job import JobListing
from app.models.application import Application
from app.modules.generation.cover_letter import cover_letter_generator
from app.modules.generation.resume_tailor import resume_tailorer
from app.modules.generation.question_answerer import question_answerer
from app.modules.generation.pdf_generator import resume_pdf_generator
from app.modules.generation.materials_pipeline import materials_pipeline

async def test_phase3():
    print("========================================")
    print("    AUTO-APPLY PHASE 3 TEST SUITE       ")
    print("  (Candidate Traceability & PDF Engine) ")
    print("========================================")

    # 1. Fetch Candidate and Job
    async with AsyncSessionLocal() as session:
        cand_res = await session.execute(select(Candidate))
        candidate = cand_res.scalars().first()
        assert candidate is not None, "Candidate profile not found in DB"

        job_res = await session.execute(select(JobListing))
        job = job_res.scalars().first()
        assert job is not None, "Job listing not found in DB"

        app_res = await session.execute(select(Application))
        app = app_res.scalars().first()
        assert app is not None, "Application not found in DB"

        candidate_profile = candidate.structured_profile or {}
        candidate_dict = {
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "location": candidate.location,
            "linkedin_url": candidate.linkedin_url,
            "github_url": candidate.github_url,
            "portfolio_url": candidate.portfolio_url,
            "structured_profile": candidate_profile
        }
        job_data = {
            "company_name": job.company_name,
            "role_title": job.role_title,
            "location": job.location,
            "job_description": job.job_description,
            "ats_platform": job.ats_platform
        }

        # 2. Test Cover Letter Generator
        print(f"\n[1/5] Generating tailored cover letter for {job.company_name} ({job.role_title})...")
        cover_letter = await cover_letter_generator.generate_cover_letter(
            candidate_profile=candidate_profile,
            job_data=job_data,
            match_rationale=job.match_rationale
        )
        assert len(cover_letter) > 100, "Cover letter too short"
        print(f"-> Cover letter generated ({len(cover_letter)} chars):")
        print("   " + cover_letter[:180].replace("\n", " ") + "...")

        # 3. Test Resume Tailorer & Bullet Emphasis
        print(f"\n[2/5] Tailoring resume bullet emphasis and skills ordering...")
        tailored_resume = await resume_tailorer.tailor_resume(
            candidate_profile=candidate_profile,
            job_data=job_data
        )
        print(f"-> Tailored Headline: {tailored_resume.get('headline')}")
        print(f"   Top Languages: {tailored_resume.get('skills', {}).get('languages', [])[:4]}")
        print(f"   Top Frameworks: {tailored_resume.get('skills', {}).get('frameworks', [])[:3]}")

        # 4. Test ATS Custom Question Answerer & Strict Source Data Traceability
        print(f"\n[3/5] Testing ATS Question Pre-Filler (Strict Traceability & Missing Field Flagging)...")
        # Custom question asking for security clearance (not in profile)
        custom_qs = [
            "Why are you interested in this role?",
            "Do you currently hold an active Top Secret Security Clearance?"
        ]
        res = await question_answerer.generate_answers(
            candidate_profile=candidate_profile,
            job_data=job_data,
            custom_questions=custom_qs
        )
        answers = res.get("answers", {})
        flagged_fields = res.get("flagged_fields", [])

        print(f"-> Sourced answers count: {len(answers)}")
        print(f"-> Flagged fields requiring candidate manual input: {len(flagged_fields)}")
        for f in flagged_fields:
            print(f"   [FLAGGED] {f.get('field') or f.get('question')}: {f.get('reason')}")

        # Assert that security clearance question was flagged and NOT guessed
        clearance_flagged = any("clearance" in (f.get("question", "").lower() + f.get("reason", "").lower()) for f in flagged_fields)
        assert clearance_flagged, "Security clearance should be flagged for manual candidate input, not guessed"

        # Test cross-referencing validation rejecting untraceable assertions
        fake_answers = {
            "university": "Massachusetts Institute of Technology (MIT)", # Fake university
            "gpa": "4.0/4.0", # Fake GPA
            "graduation_date": "December 2030" # Fake date
        }
        val_check = question_answerer.validate_traceability(fake_answers, candidate_profile)
        print(f"-> Testing traceability validator on untraceable answers: Passed={val_check['passed']}, Rejected count={len(val_check['rejected_answers'])}")
        assert val_check["passed"] is False, "Validator must reject untraceable facts"
        assert len(val_check["rejected_answers"]) > 0, "Validator must flag untraceable answers"

        # 5. Test Playwright Single-Page ATS PDF Compiler
        print(f"\n[4/5] Compiling pristine single-page ATS PDF via Playwright...")
        pdf_path = await resume_pdf_generator.generate_pdf(
            application_id="test_phase3_app",
            candidate=candidate_dict,
            tailored_data=tailored_resume
        )
        assert os.path.exists(pdf_path), f"PDF file not found at {pdf_path}"
        file_size = os.path.getsize(pdf_path)
        print(f"-> Generated ATS PDF: {pdf_path} ({file_size} bytes)")
        assert file_size > 5000, "Generated PDF file size is suspiciously small"

        # 6. Test Full Materials Pipeline on Application
        print(f"\n[5/5] Executing full materials pipeline for Application ID: {app.id}...")
        pipeline_res = await materials_pipeline.prepare_application_materials(app.id)
        assert pipeline_res.get("status") == "success"
        print(f"-> Pipeline result: {pipeline_res['status']} for {pipeline_res['company']}")

    print("\n========================================")
    print("   ALL PHASE 3 UNIT TESTS PASSED!       ")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(test_phase3())
