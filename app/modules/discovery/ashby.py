import re
import html
import httpx
from typing import List, Dict, Any
import logging

logger = logging.getLogger("AshbyDiscovery")

class AshbyClient:
    API_URL = "https://api.ashbyhq.com/posting-api/job-board"

    def _clean_html(self, raw_html: str) -> str:
        if not raw_html:
            return ""
        clean = re.sub(r'<(script|style).*?</\1>', '', raw_html, flags=re.DOTALL)
        clean = re.sub(r'<(br|p|li)[^>]*>', '\n', clean)
        clean = re.sub(r'<[^>]+>', '', clean)
        clean = html.unescape(clean)
        return re.sub(r'\n\s*\n', '\n\n', clean).strip()

    async def fetch_company_jobs(self, company_slug: str) -> List[Dict[str, Any]]:
        """Fetch public job listings from Ashby."""
        url = f"{self.API_URL}/{company_slug}"
        jobs = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                if response.status_code == 404:
                    logger.warning(f"Ashby board not found for: {company_slug}")
                    return []
                response.raise_for_status()
                data = response.json()

                for item in data.get("jobs", []):
                    title = item.get("title", "").strip()
                    location = item.get("locationName") or item.get("location", "Remote")
                    if item.get("isRemote"):
                        location += " (Remote)"
                    job_url = item.get("jobUrl") or f"https://jobs.ashbyhq.com/{company_slug}/{item.get('id')}"
                    ats_job_id = str(item.get("id", ""))
                    description_clean = self._clean_html(item.get("descriptionHtml", ""))

                    title_lower = title.lower()
                    is_intern = any(kw in title_lower for kw in [
                        "intern", "internship", "co-op", "coop", "student", 
                        "early career", "apprentice", "university", "new grad"
                    ])

                    jobs.append({
                        "company_name": company_slug.capitalize(),
                        "company_slug": company_slug,
                        "role_title": title,
                        "location": location,
                        "ats_platform": "ashby",
                        "job_url": job_url,
                        "ats_job_id": ats_job_id,
                        "job_description": description_clean,
                        "is_internship": is_intern,
                        "requirements": []
                    })
        except Exception as e:
            logger.error(f"Error fetching Ashby jobs for '{company_slug}': {e}")

        return jobs

ashby_client = AshbyClient()
