import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.application import Application
from app.models.job import JobListing
from app.models.email_log import EmailLog
from app.modules.watcher.classifier import email_classifier
from app.modules.watcher.sync import watcher_sync_service

async def test_phase4():
    print("========================================")
    print("    AUTO-APPLY PHASE 4 TEST SUITE       ")
    print("========================================")

    # 1. Test Email Classifier directly with an Interview Invite
    print("\n[1/4] Testing Gemini Recruiter Email Intent Classifier...")
    mock_active_apps = [
        {"id": "app-1", "company_name": "Stripe", "role_title": "Software Engineering Intern", "status": "applied"},
        {"id": "app-2", "company_name": "Ramp", "role_title": "Full Stack Intern", "status": "applied"}
    ]

    interview_email = {
        "sender": "recruiting@stripe.com",
        "subject": "Update regarding your Software Engineering Intern application at Stripe",
        "snippet": "Hi Alex, our team was very impressed with your background! We would like to invite you to a 45-minute technical interview.",
        "body_text": "Hi Alex, thank you for applying for the Software Engineering Intern role at Stripe. We would like to schedule a 45-minute technical screen next week to discuss your distributed systems background. Please let us know your availability."
    }

    classification = await email_classifier.classify_and_match(interview_email, mock_active_apps)
    print(f"-> Matched Company: {classification.get('matched_company_name')}")
    print(f"   Category: {classification.get('category')}")
    print(f"   Suggested Status: {classification.get('suggested_status')}")
    print(f"   Summary Snippet: {classification.get('summary_snippet')}")
    assert classification.get("category") == "interview_invite"
    assert classification.get("suggested_status") == "interview"

    # 2. Test Rejection Email Classification
    print("\n[2/4] Testing Rejection Email Classification...")
    rejection_email = {
        "sender": "no-reply@ramp.com",
        "subject": "Your application to Ramp",
        "snippet": "Thank you for taking the time to apply. After careful review, we have decided not to move forward with your candidacy.",
        "body_text": "Thank you for taking the time to apply for the Full Stack Intern position at Ramp. While your background is impressive, we have decided to move forward with other candidates."
    }

    rej_class = await email_classifier.classify_and_match(rejection_email, mock_active_apps)
    print(f"-> Matched Company: {rej_class.get('matched_company_name')}")
    print(f"   Category: {rej_class.get('category')}")
    print(f"   Suggested Status: {rej_class.get('suggested_status')}")
    assert rej_class.get("category") == "rejection"
    assert rej_class.get("suggested_status") == "rejected"

    # 3. Test End-to-End Watcher Sync on Database Record
    print("\n[3/4] Testing Watcher Sync Service on active database application...")
    async with AsyncSessionLocal() as session:
        # Find Stripe application in DB
        app_res = await session.execute(
            select(Application).join(Application.job).where(JobListing.company_name == "Stripe")
        )
        stripe_app = app_res.scalars().first()
        assert stripe_app is not None, "Stripe application not found in DB"
        
        # Reset status for test
        stripe_app.status = "applied"
        await session.commit()

        test_msg_id = f"test_msg_{uuid.uuid4().hex[:8]}"
        sync_payload = {
            "message_id": test_msg_id,
            "thread_id": "thread_stripe_123",
            "sender": "university-recruiting@stripe.com",
            "subject": "Stripe Internship Interview Invitation",
            "snippet": "We would love to invite you to an interview screen for Software Engineering Intern.",
            "body_text": "Hi Alex, we reviewed your resume and projects and would love to move forward with an interview screen.",
            "received_at": datetime.utcnow()
        }

        result = await watcher_sync_service.process_incoming_email(sync_payload)
        print(f"-> Sync Result: {result['status']}, Category: {result['category']}")
        assert result["category"] == "interview_invite"

        # Verify application status in DB
        await session.refresh(stripe_app)
        print(f"-> Updated Application Status in DB: '{stripe_app.status}'")
        print(f"-> Last Reply Snippet: '{stripe_app.last_reply_snippet}'")
        assert stripe_app.status == "interview"

        # 4. Test Idempotency (prevent duplicate processing of same message_id)
        print("\n[4/4] Testing Idempotency on duplicate message_id...")
        dup_result = await watcher_sync_service.process_incoming_email(sync_payload)
        print(f"-> Duplicate run result: {dup_result['status']} (reason: {dup_result.get('reason')})")
        assert dup_result["status"] == "skipped"

    print("\n========================================")
    print("   ALL PHASE 4 UNIT TESTS PASSED!       ")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(test_phase4())
