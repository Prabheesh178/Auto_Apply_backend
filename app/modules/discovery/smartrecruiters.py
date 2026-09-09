import re
import html
import httpx
from typing import List, Dict, Any
import logging

logger = logging.getLogger("SmartRecruitersDiscovery")

class SmartRecruitersClient:
    BASE_URL = "https://api.smartrecruiters.com/v1/companies"

    def _clean_html(self, raw_html: str) -> str:
        if not raw_html:
            return ""
        clean = re.sub(r'<(script|style).*?</\1>', '', raw_html, flags=re.DOTALL)
        clean = re.sub(r'<(br|p|li)[^>]*>', '\n', clean)
        clean = re.sub(r'<[^>]+>', '', clean)
        clean = html.unescape(clean)
        return re.sub(r'\n\s*\n', '\n\n', clean).strip()

    async def fetch_company_jobs(self, company_slug: str) -> List[Dict[str, Any]]:
        """Fetch public job listings from SmartRecruiters."""
        url = f"{self.BASE_URL}/{company_slug}/postings"
        jobs = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                if response.status_code == 404:
                    logger.warning(f"SmartRecruiters board not found for: {company_slug}")
                    return []
                response.raise_for_status()
                data = response.json()

                for item in data.get("content", []):
                    title = item.get("name", "").strip()
                    loc_obj = item.get("location", {})
                    city = loc_obj.get("city", "")
                    country = loc_obj.get("country", "")
                    location = f"{city}, {country}".strip(", ") if (city or country) else "Remote"
                    
                    ats_job_id = str(item.get("id", ""))
                    job_url = f"https://jobs.smartrecruiters.com/{company_slug}/{ats_job_id}"

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
                        "ats_platform": "smartrecruiters",
                        "job_url": job_url,
                        "ats_job_id": ats_job_id,
                        "job_description": f"Role at {company_slug.capitalize()}: {title}",
                        "is_internship": is_intern,
                        "requirements": []
                    })
        except Exception as e:
            logger.error(f"Error fetching SmartRecruiters jobs for '{company_slug}': {e}")

        return jobs

smartrecruiters_client = SmartRecruitersClient()
