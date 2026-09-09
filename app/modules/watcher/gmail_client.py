import os
import base64
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.config import settings

logger = logging.getLogger("GmailClient")

class GmailClient:
    def __init__(self):
        self.credentials_file = settings.GMAIL_CREDENTIALS_FILE
        self.token_file = settings.GMAIL_TOKEN_FILE
        self.service = None
        self._init_service()

    def _init_service(self):
        """Initializes Google Gmail API service if token/credentials exist."""
        if not os.path.exists(self.token_file):
            logger.info("Gmail token.json not found. Watcher running in simulation/read-ready mode.")
            return

        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from google.auth.transport.requests import Request

            creds = Credentials.from_authorized_user_file(self.token_file, [
                'https://www.googleapis.com/auth/gmail.readonly'
            ])

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API service connected successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize Gmail API service: {e}")

    def is_connected(self) -> bool:
        return self.service is not None

    async def fetch_recent_recruiter_emails(self, max_results: int = 25) -> List[Dict[str, Any]]:
        """
        Polls Gmail for recruiter messages matching keywords from the last 7 days.
        """
        if not self.is_connected():
            return []

        try:
            # Query for typical ATS and recruiter subjects
            query = '("thank you for applying" OR "application" OR "interview" OR "status" OR "recruiting" OR "update")'
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            emails = []

            for msg_meta in messages:
                msg_id = msg_meta['id']
                msg = self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()

                payload = msg.get('payload', {})
                headers = payload.get('headers', [])
                header_dict = {h['name'].lower(): h['value'] for h in headers}

                subject = header_dict.get('subject', 'No Subject')
                sender = header_dict.get('from', 'Unknown Sender')
                date_str = header_dict.get('date')

                snippet = msg.get('snippet', '')
                thread_id = msg.get('threadId', '')

                # Extract body
                body_text = self._extract_body(payload)

                received_at = datetime.utcnow()
                if date_str:
                    try:
                        from email.utils import parsedate_to_datetime
                        received_at = parsedate_to_datetime(date_str)
                    except Exception:
                        pass

                emails.append({
                    "message_id": msg_id,
                    "thread_id": thread_id,
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet,
                    "body_text": body_text or snippet,
                    "received_at": received_at
                })

            return emails
        except Exception as e:
            logger.error(f"Error fetching Gmail messages: {e}")
            return []

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extracts plain text body from multipart or single part MIME payload."""
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='ignore')
        else:
            data = payload.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='ignore')
        return ""

gmail_client = GmailClient()
