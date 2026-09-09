import os
import logging
from typing import Dict, Any
from playwright.async_api import Page
from app.modules.automation.browser_engine import browser_engine

logger = logging.getLogger("LeverFiller")

class LeverFiller:
    async def fill_form(
        self,
        page: Page,
        candidate_data: Dict[str, Any],
        cover_letter: str,
        resume_pdf_path: str,
        form_answers: Dict[str, Any]
    ) -> bool:
        """Direct, functional filling of Lever ATS application form inputs without submitting."""
        try:
            edu_institution = ""
            if candidate_data.get("education") and len(candidate_data["education"]) > 0:
                edu_institution = candidate_data["education"][0].get("institution", "")

            # 1. Standard Fields (Direct Fill)
            for selector, val in [
                ("input[name='name']", candidate_data.get("full_name", "")),
                ("input[name='email']", candidate_data.get("email", "")),
                ("input[name='phone']", candidate_data.get("phone", "")),
                ("input[name='org']", edu_institution)
            ]:
                if val and await page.query_selector(selector):
                    await browser_engine.direct_fill(page, selector, val)

            # 2. Upload Resume PDF
            if resume_pdf_path and os.path.exists(resume_pdf_path):
                file_input = await page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(resume_pdf_path)
                    logger.info(f"Attached resume file to Lever: {resume_pdf_path}")

            # 3. Social / Portfolio Links
            links_map = [
                ("input[name*='LinkedIn' i]", candidate_data.get("linkedin_url")),
                ("input[name*='GitHub' i]", candidate_data.get("github_url")),
                ("input[name*='Portfolio' i], input[name*='Website' i]", candidate_data.get("portfolio_url"))
            ]
            for sel, link_val in links_map:
                if link_val and await page.query_selector(sel):
                    await browser_engine.direct_fill(page, sel, link_val)

            # 4. Comments / Cover Letter Area
            if cover_letter:
                cl_selectors = ["textarea[name='comments']", "textarea[name*='additional' i]", "textarea"]
                for sel in cl_selectors:
                    el = await page.query_selector(sel)
                    if el:
                        await el.fill(cover_letter)
                        break

            logger.info("Lever form fields prefilled successfully.")
            return True
        except Exception as e:
            logger.error(f"Error filling Lever form: {e}")
            return False

lever_filler = LeverFiller()
