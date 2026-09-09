import uuid
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models.application import Application
from app.models.job import JobListing
from app.models.email_log import EmailLog
from app.modules.watcher.gmail_client import gmail_client
from app.modules.watcher.classifier import email_classifier
from app.services.activity_service import activity_service

class WatcherSyncService:
    async def process_incoming_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a single incoming recruiter email:
        1. Checks for duplicate message_id
        2. Classifies intent with Gemini
        3. Updates matched application status and reply snippet
        4. Logs email to database
        5. Emits SSE activity event
        """
        msg_id = email_data.get("message_id") or str(uuid.uuid4())

        async with AsyncSessionLocal() as session:
            # Check for existing processed email
            existing_stmt = select(EmailLog).where(EmailLog.message_id == msg_id)
            existing_res = await session.execute(existing_stmt)
            if existing_res.scalar_one_or_none():
                return {"status": "skipped", "reason": "already_processed", "message_id": msg_id}

            # Fetch active applications with jobs
            apps_stmt = select(Application).join(Application.job).options(selectinload(Application.job))
            apps_res = await session.execute(apps_stmt)
            all_apps = apps_res.scalars().all()

            apps_summary = [
                {
                    "id": app.id,
                    "company_name": app.job.company_name if app.job else "",
                    "role_title": app.job.role_title if app.job else "",
                    "status": app.status
                }
                for app in all_apps
            ]

            # Classify email intent with Gemini
            classification = await email_classifier.classify_and_match(email_data, apps_summary)

            matched_app_id = classification.get("matched_application_id")
            suggested_status = classification.get("suggested_status")
            category = classification.get("category", "general")
            snippet = classification.get("summary_snippet") or email_data.get("snippet", "")
            company_name = classification.get("matched_company_name", "Company")

            matched_app = None
            if matched_app_id:
                for a in all_apps:
                    if a.id == matched_app_id:
                        matched_app = a
                        break

            # Update application status if valid transition
            if matched_app:
                if suggested_status and suggested_status != "no_change":
                    matched_app.status = suggested_status
                matched_app.last_reply_snippet = snippet
                matched_app.last_reply_at = email_data.get("received_at") or datetime.utcnow()
                matched_app.updated_at = datetime.utcnow()

            # Record email log
            log_entry = EmailLog(
                id=str(uuid.uuid4()),
                application_id=matched_app.id if matched_app else None,
                message_id=msg_id,
                thread_id=email_data.get("thread_id"),
                sender=email_data.get("sender", "Unknown"),
                subject=email_data.get("subject", "Recruiter Email"),
                snippet=snippet,
                body_text=email_data.get("body_text", ""),
                received_at=email_data.get("received_at") or datetime.utcnow(),
                category=category,
                confidence_score=classification.get("confidence_score", 1.0)
            )
            session.add(log_entry)
            await session.commit()

            # Activity Log level
            level = "SUCCESS" if category == "interview_invite" else "INFO" if category in ["ack", "assessment"] else "WARN"
            await activity_service.log(
                level,
                "Watcher",
                f"Gmail Watcher matched message from {company_name}: [{category.upper()}] \"{snippet}\"",
                {
                    "application_id": matched_app.id if matched_app else None,
                    "category": category,
                    "new_status": matched_app.status if matched_app else None
                }
            )

            return {
                "status": "processed",
                "message_id": msg_id,
                "category": category,
                "matched_company": company_name,
                "new_status": matched_app.status if matched_app else None,
                "snippet": snippet
            }

    async def sync_all_recent_emails(self) -> Dict[str, Any]:
        """Polls Gmail client and processes all recent emails."""
        emails = await gmail_client.fetch_recent_recruiter_emails()
        if not emails:
            return {"status": "success", "processed_count": 0, "message": "No new recruiter emails found or Gmail offline"}

        processed = []
        for em in emails:
            res = await self.process_incoming_email(em)
            processed.append(res)

        return {
            "status": "success",
            "processed_count": len(processed),
            "results": processed
        }

watcher_sync_service = WatcherSyncService()
