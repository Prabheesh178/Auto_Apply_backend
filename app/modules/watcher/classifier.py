import json
import re
from typing import Dict, Any, List, Optional
from app.services.gemini_service import gemini_service

class EmailClassifier:
    async def classify_and_match(
        self,
        email_data: Dict[str, Any],
        active_applications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Uses Gemini to match an incoming email to a specific application and classify recruiter intent.
        """
        sender = email_data.get("sender", "")
        subject = email_data.get("subject", "")
        snippet = email_data.get("snippet", "")
        body = email_data.get("body_text", "")[:2000]

        apps_summary = [
            {
                "id": app.get("id"),
                "company_name": app.get("company_name"),
                "role_title": app.get("role_title"),
                "current_status": app.get("status")
            }
            for app in active_applications
        ]

        system_instruction = (
            "You are an expert recruitment coordinator AI. "
            "Analyze the incoming recruiter email and match it to one of the candidate's active job applications. "
            "Classify the email intent accurately into one of: 'interview_invite', 'rejection', 'assessment', 'ack', 'general'. "
            "Map intent to target application status: 'interview', 'rejected', 'applied', or 'no_change'. "
            "Extract a clean 1-sentence summary snippet for the dashboard. Return ONLY valid JSON."
        )

        prompt = f"""
Incoming Email:
- From: {sender}
- Subject: {subject}
- Snippet: {snippet}
- Body:
{body}

Active Applications:
{json.dumps(apps_summary, indent=2)}

Return JSON adhering to this schema:
{{
  "matched_application_id": "string or null",
  "matched_company_name": "string",
  "category": "interview_invite | rejection | assessment | ack | general",
  "suggested_status": "interview | rejected | applied | no_change",
  "summary_snippet": "Clean 1-2 sentence recruiter summary or next step",
  "confidence_score": 0.95
}}
"""

        try:
            if gemini_service.is_available():
                result = await gemini_service.generate_json(prompt, system_instruction)
                if result and "category" in result:
                    return result
        except Exception as e:
            print(f"[EmailClassifier] Gemini classification error: {e}")

        # Deterministic fallback classifier
        return self._heuristic_fallback(email_data, active_applications)

    def _heuristic_fallback(
        self,
        email_data: Dict[str, Any],
        active_applications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Keyword and regex matching fallback."""
        subject = email_data.get("subject", "").lower()
        sender = email_data.get("sender", "").lower()
        body = email_data.get("body_text", "").lower()
        text = f"{subject} {sender} {body}"

        # 1. Match application by company name in subject/sender/body
        matched_app = None
        for app in active_applications:
            comp = app.get("company_name", "").lower()
            if comp and (comp in subject or comp in sender or comp in text):
                matched_app = app
                break

        # 2. Determine category & status
        if any(term in text for term in ["interview", "invitation", "screen", "chat", "technical interview", "speak with you", "schedule time"]):
            category = "interview_invite"
            status = "interview"
            snippet = f"Received interview invitation from {matched_app.get('company_name') if matched_app else 'Recruiter'}."
        elif any(term in text for term in ["not moving forward", "unfortunate", "other candidates", "regret to inform", "chosen not to move", "decided not to proceed"]):
            category = "rejection"
            status = "rejected"
            snippet = f"Application not moving forward at {matched_app.get('company_name') if matched_app else 'Company'}."
        elif any(term in text for term in ["hackerrank", "codesignal", "assessment", "online test", "coding challenge"]):
            category = "assessment"
            status = "applied"
            snippet = f"Technical assessment received for {matched_app.get('role_title') if matched_app else 'role'}."
        elif any(term in text for term in ["thank you for applying", "application received", "received your application", "we have received"]):
            category = "ack"
            status = "applied"
            snippet = f"Application acknowledgment confirmed by {matched_app.get('company_name') if matched_app else 'ATS'}."
        else:
            category = "general"
            status = "no_change"
            snippet = email_data.get("snippet", "Update received.")[:120]

        return {
            "matched_application_id": matched_app.get("id") if matched_app else None,
            "matched_company_name": matched_app.get("company_name") if matched_app else "Company",
            "category": category,
            "suggested_status": status,
            "summary_snippet": snippet,
            "confidence_score": 0.85 if matched_app else 0.5
        }

email_classifier = EmailClassifier()
