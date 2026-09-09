import os
import logging
from typing import Dict, Any
from playwright.async_api import Page
from app.modules.automation.browser_engine import browser_engine

logger = logging.getLogger("SmartRecruitersFiller")

class SmartRecruitersFiller:
    async def fill_form(
        self,
        page: Page,
        candidate_data: Dict[str, Any],
        cover_letter: str,
        resume_pdf_path: str,
        form_answers: Dict[str, Any]
    ) -> bool:
        """Direct, functional filling of SmartRecruiters ATS application form inputs without submitting."""
        try:
            full_name = candidate_data.get("full_name", "")
            name_parts = full_name.split(" ", 1) if full_name else ["", ""]
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # 1. Standard Fields (Direct Fill)
            for selector, val in [
                ("input[name*='firstName' i], input[id*='first' i]", first_name),
                ("input[name*='lastName' i], input[id*='last' i]", last_name),
                ("input[name*='email' i], input[type='email']", candidate_data.get("email", "")),
                ("input[name*='phone' i], input[type='tel']", candidate_data.get("phone", ""))
            ]:
                if val and await page.query_selector(selector):
                    await browser_engine.direct_fill(page, selector, val)

            # 2. Upload Resume PDF
            if resume_pdf_path and os.path.exists(resume_pdf_path):
                file_input = await page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(resume_pdf_path)
                    logger.info(f"Attached resume file to SmartRecruiters: {resume_pdf_path}")

            # 3. Message / Cover letter
            if cover_letter:
                el = await page.query_selector("textarea")
                if el:
                    await el.fill(cover_letter)

            logger.info("SmartRecruiters form fields prefilled successfully.")
            return True
        except Exception as e:
            logger.error(f"Error filling SmartRecruiters form: {e}")
            return False

smartrecruiters_filler = SmartRecruitersFiller()
