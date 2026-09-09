import os
import logging
from typing import Dict, Any
from playwright.async_api import Page
from app.modules.automation.browser_engine import browser_engine

logger = logging.getLogger("GenericFiller")

class GenericFiller:
    async def fill_form(
        self,
        page: Page,
        candidate_data: Dict[str, Any],
        cover_letter: str,
        resume_pdf_path: str,
        form_answers: Dict[str, Any]
    ) -> bool:
        """Direct, functional semantic filler for direct company forms without submitting."""
        try:
            full_name = candidate_data.get("full_name", "")
            name_parts = full_name.split(" ", 1) if full_name else ["", ""]
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # Fill name fields
            if await page.query_selector("input[name*='first' i], input[id*='first' i]"):
                await browser_engine.direct_fill(page, "input[name*='first' i], input[id*='first' i]", first_name)
                if await page.query_selector("input[name*='last' i], input[id*='last' i]"):
                    await browser_engine.direct_fill(page, "input[name*='last' i], input[id*='last' i]", last_name)
            elif await page.query_selector("input[name*='name' i], input[id*='name' i]"):
                await browser_engine.direct_fill(page, "input[name*='name' i], input[id*='name' i]", full_name)

            # Fill email & phone
            if await page.query_selector("input[type='email'], input[name*='email' i]"):
                await browser_engine.direct_fill(page, "input[type='email'], input[name*='email' i]", candidate_data.get("email", ""))

            if await page.query_selector("input[type='tel'], input[name*='phone' i]"):
                await browser_engine.direct_fill(page, "input[type='tel'], input[name*='phone' i]", candidate_data.get("phone", ""))

            # Upload resume
            if resume_pdf_path and os.path.exists(resume_pdf_path):
                file_input = await page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(resume_pdf_path)

            # Cover letter
            if cover_letter:
                el = await page.query_selector("textarea")
                if el:
                    await el.fill(cover_letter)

            logger.info("Generic form fields prefilled successfully.")
            return True
        except Exception as e:
            logger.error(f"Error in Generic form filler: {e}")
            return False

generic_filler = GenericFiller()
