import re
import html
import httpx
from typing import List, Dict, Any
import logging

logger = logging.getLogger("LeverDiscovery")

class LeverClient:
    BASE_URL = "https://api.lever.co/v0/postings"

    def _clean_html(self, raw_html: str) -> str:
        if not raw_html:
            return ""
        clean = re.sub(r'<(script|style).*?</\1>', '', raw_html, flags=re.DOTALL)
        clean = re.sub(r'<(br|p|li)[^>]*>', '\n', clean)
        clean = re.sub(r'<[^>]+>', '', clean)
        clean = html.unescape(clean)
        return re.sub(r'\n\s*\n', '\n\n', clean).strip()

    async def fetch_company_jobs(self, company_slug: str) -> List[Dict[str, Any]]:
        """Fetch public job postings from Lever."""
        url = f"{self.BASE_URL}/{company_slug}?mode=json"
        jobs = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                if response.status_code == 404:
                    logger.warning(f"Lever board not found for: {company_slug}")
                    return []
                response.raise_for_status()
                data = response.json()

                for item in data:
                    title = item.get("text", "").strip()
                    categories = item.get("categories", {})
                    location = categories.get("location") or categories.get("allLocations", ["Remote"])[0] if categories.get("allLocations") else "Remote"
                    job_url = item.get("hostedUrl", "")
                    ats_job_id = str(item.get("id", ""))
                    description_plain = item.get("descriptionPlain") or self._clean_html(item.get("description", ""))

                    # Extract requirements lists if available
                    requirements = []
                    for req_group in item.get("lists", []):
                        group_text = req_group.get("text", "")
                        content = self._clean_html(req_group.get("content", ""))
                        if content:
                            requirements.append(f"{group_text}: {content}")

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
                        "ats_platform": "lever",
                        "job_url": job_url,
                        "ats_job_id": ats_job_id,
                        "job_description": description_plain,
                        "is_internship": is_intern,
                        "requirements": requirements
                    })
        except Exception as e:
            logger.error(f"Error fetching Lever jobs for '{company_slug}': {e}")

        return jobs

lever_client = LeverClient()
