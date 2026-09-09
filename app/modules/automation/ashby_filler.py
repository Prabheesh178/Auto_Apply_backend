import os
import logging
from typing import Dict, Any
from playwright.async_api import Page
from app.modules.automation.browser_engine import browser_engine

logger = logging.getLogger("AshbyFiller")

class AshbyFiller:
    async def fill_form(
        self,
        page: Page,
        candidate_data: Dict[str, Any],
        cover_letter: str,
        resume_pdf_path: str,
        form_answers: Dict[str, Any]
    ) -> bool:
        """Direct, functional filling of Ashby ATS application form inputs without submitting."""
        try:
            # 1. Standard Fields (Direct Fill)
            for selector, val in [
                ("input[name*='name' i]", candidate_data.get("full_name", "")),
                ("input[name*='email' i]", candidate_data.get("email", "")),
                ("input[name*='phone' i]", candidate_data.get("phone", ""))
            ]:
                if val and await page.query_selector(selector):
                    await browser_engine.direct_fill(page, selector, val)

            # 2. Upload Resume PDF
            if resume_pdf_path and os.path.exists(resume_pdf_path):
                file_input = await page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(resume_pdf_path)
                    logger.info(f"Attached resume file to Ashby: {resume_pdf_path}")

            # 3. Links & Cover Letter
            if candidate_data.get("linkedin_url"):
                el = await page.query_selector("input[placeholder*='linkedin' i], input[name*='linkedin' i]")
                if el:
                    await browser_engine.direct_fill(page, "input[placeholder*='linkedin' i], input[name*='linkedin' i]", candidate_data["linkedin_url"])

            if cover_letter:
                el = await page.query_selector("textarea")
                if el:
                    await el.fill(cover_letter)

            logger.info("Ashby form fields prefilled successfully.")
            return True
        except Exception as e:
            logger.error(f"Error filling Ashby form: {e}")
            return False

ashby_filler = AshbyFiller()
