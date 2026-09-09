import re
import html
import httpx
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger("GreenhouseDiscovery")

class GreenhouseClient:
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def _clean_html(self, raw_html: str) -> str:
        """Strip HTML tags and unescape HTML entities into clean readable text."""
        if not raw_html:
            return ""
        # Remove script and style elements
        clean = re.sub(r'<(script|style).*?</\1>', '', raw_html, flags=re.DOTALL)
        # Convert <br>, <p>, <li> to newlines
        clean = re.sub(r'<(br|p|li)[^>]*>', '\n', clean)
        # Strip all other tags
        clean = re.sub(r'<[^>]+>', '', clean)
        # Unescape entities
        clean = html.unescape(clean)
        # Normalize whitespace
        clean = re.sub(r'\n\s*\n', '\n\n', clean).strip()
        return clean

    async def fetch_company_jobs(self, company_slug: str) -> List[Dict[str, Any]]:
        """Fetch all public job postings for a company from Greenhouse."""
        url = f"{self.BASE_URL}/{company_slug}/jobs?content=true"
        jobs = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                if response.status_code == 404:
                    logger.warning(f"Greenhouse board not found for company slug: {company_slug}")
                    return []
                response.raise_for_status()
                data = response.json()
                
                raw_jobs = data.get("jobs", [])
                for item in raw_jobs:
                    title = item.get("title", "").strip()
                    location = item.get("location", {}).get("name", "Remote")
                    job_url = item.get("absolute_url", "")
                    ats_job_id = str(item.get("id", ""))
                    raw_content = item.get("content", "")
                    description_clean = self._clean_html(raw_content)

                    # Determine if it's an internship or early career role
                    title_lower = title.lower()
                    is_intern = any(kw in title_lower for kw in [
                        "intern", "internship", "co-op", "coop", "student", 
                        "early career", "apprentice", "university grad", "new grad"
                    ])

                    jobs.append({
                        "company_name": company_slug.capitalize(),
                        "company_slug": company_slug,
                        "role_title": title,
                        "location": location,
                        "ats_platform": "greenhouse",
                        "job_url": job_url,
                        "ats_job_id": ats_job_id,
                        "job_description": description_clean,
                        "is_internship": is_intern,
                        "requirements": []
                    })
        except Exception as e:
            logger.error(f"Error fetching Greenhouse jobs for '{company_slug}': {e}")

        return jobs

greenhouse_client = GreenhouseClient()
