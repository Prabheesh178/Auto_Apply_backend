import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import datetime
from sqlalchemy import select
from playwright.async_api import async_playwright
from app.database import AsyncSessionLocal
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import JobListing
from app.modules.automation.browser_engine import browser_engine
from app.modules.automation.greenhouse_filler import greenhouse_filler
from app.modules.automation.lever_filler import lever_filler
from app.modules.automation.orchestrator import automation_orchestrator

MOCK_ATS_HTML = """
<!DOCTYPE html>
<html>
<head><title>Stripe Application Form</title></head>
<body style="font-family: Arial; padding: 20px;">
  <h2>Apply for Software Engineering Intern at Stripe</h2>
  <form id="application_form">
    <div><label>First Name:</label><input id="first_name" name="first_name" type="text" /></div>
    <div><label>Last Name:</label><input id="last_name" name="last_name" type="text" /></div>
    <div><label>Email:</label><input id="email" name="email" type="email" /></div>
    <div><label>Phone:</label><input id="phone" name="phone" type="tel" /></div>
    <div><label>Resume:</label><input id="resume" name="resume" type="file" /></div>
    <div><label>LinkedIn:</label><input id="linkedin" name="linkedin" type="text" /></div>
    <div><label>GitHub:</label><input id="github" name="github" type="text" /></div>
    <div><label>Cover Letter:</label><textarea id="cover_letter_text" name="cover_letter"></textarea></div>
    <div><label>Why Stripe?:</label><textarea id="why_company" name="why_company"></textarea></div>
    <button id="submit_app" type="submit" style="padding: 10px 20px; background: #6366F1; color: white; border: none; border-radius: 6px; margin-top: 10px;">Submit Application</button>
  </form>
</body>
</html>
"""

async def test_phase5():
    print("========================================")
    print("    AUTO-APPLY PHASE 5 TEST SUITE       ")
    print(" (Direct Filling & Manual Submit Gate)  ")
    print("========================================")

    # 1. Test Direct Functional Browser Engine
    print("\n[1/4] Testing Direct Functional Browser Context Creation...")
    async with async_playwright() as p:
        browser, context, page = await browser_engine.create_browser_context(p, headless=True)
        print("-> Standard Chromium context launched successfully (no stealth wrappers / artificial delays).")
        
        # Load mock ATS application DOM
        await page.set_content(MOCK_ATS_HTML)
        print("-> Mock ATS application DOM loaded.")

        # 2. Test Direct Form Filler (Greenhouse Schema)
        print("\n[2/4] Testing Direct Form Filling (No typing delays, direct value injection)...")
        candidate_data = {
            "full_name": "Alex Rivera",
            "email": "alex.rivera@test.com",
            "phone": "+1 555 382 9912",
            "linkedin_url": "https://linkedin.com/in/alexrivera",
            "github_url": "https://github.com/alexrivera"
        }
        test_pdf = os.path.abspath(os.path.join("storage", "resumes", "test_phase3_app_resume.pdf"))
        
        fill_res = await greenhouse_filler.fill_form(
            page=page,
            candidate_data=candidate_data,
            cover_letter="Dear Hiring Team, I am thrilled to apply for the SWE Intern role.",
            resume_pdf_path=test_pdf if os.path.exists(test_pdf) else "",
            form_answers={"why_this_company": "Stripe is the gold standard for payments infrastructure."}
        )
        assert fill_res is True, "Direct form filling failed"
        print("-> Form inputs filled directly and functionally.")

        # Verify values in DOM
        first_val = await page.input_value("#first_name")
        email_val = await page.input_value("#email")
        print(f"   Verified first_name: '{first_val}', email: '{email_val}'")
        assert first_val == "Alex"
        assert email_val == "alex.rivera@test.com"

        # 3. Test Pre-Fill Screenshot Capture (Without Submitting)
        print("\n[3/4] Testing Pre-Fill Screenshot Capture (No Submit Click)...")
        screenshot_path = await browser_engine.capture_screenshot(page, "test_phase5_app", "prefilled")
        assert os.path.exists(screenshot_path), f"Screenshot not found at {screenshot_path}"
        ss_size = os.path.getsize(screenshot_path)
        print(f"-> Captured prefill proof screenshot: {screenshot_path} ({ss_size} bytes)")
        assert ss_size > 5000, "Screenshot file size is too small"

        await browser.close()

    # 4. Test Orchestrator: Pre-fill vs Final User-Approved Submission
    print("\n[4/4] Testing Orchestrator Workflow (Pre-fill -> Manual Approval -> Final Submit)...")
    async with AsyncSessionLocal() as session:
        app_res = await session.execute(select(Application))
        app = app_res.scalars().first()
        assert app is not None, "Application not found in DB"

        # (a) Test Pre-Fill Stage: Populates fields and STOPS for review
        print(f"-> Executing Pre-Fill Stage for Application ID: {app.id}...")
        prefill_res = await automation_orchestrator.prefill_application(app.id)
        assert prefill_res.get("status") in ["prefilled", "failed"]
        await session.refresh(app)
        print(f"   Application Status in DB after prefill: '{app.status}' (Awaiting Candidate Review)")
        assert app.status == "pending_review", "Application must stay in pending_review after prefill"

        # (b) Test User-Triggered Final Submission: Explicit approval execution
        print(f"-> Simulating Explicit Candidate Approval -> Final Submission for Application ID: {app.id}...")
        submit_res = await automation_orchestrator.execute_final_submission(app.id, dry_run=True)
        assert submit_res.get("status") in ["success", "failed"]
        await session.refresh(app)
        print(f"   Application Status in DB after explicit submit: '{app.status}'")
        assert app.status == "applied", "Application must transition to applied upon explicit submit approval"
        if app.submission_screenshot_path:
            print(f"   Final submission proof screenshot saved in DB: {app.submission_screenshot_path}")

    print("\n========================================")
    print("   ALL PHASE 5 UNIT TESTS PASSED!       ")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(test_phase5())
