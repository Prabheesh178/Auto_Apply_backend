import os
import logging
from typing import Dict, Any
from playwright.async_api import Page
from app.modules.automation.browser_engine import browser_engine

logger = logging.getLogger("GreenhouseFiller")

class GreenhouseFiller:
    async def fill_form(
        self,
        page: Page,
        candidate_data: Dict[str, Any],
        cover_letter: str,
        resume_pdf_path: str,
        form_answers: Dict[str, Any]
    ) -> bool:
        """Direct, functional filling of Greenhouse ATS application form inputs without submitting."""
        try:
            full_name = candidate_data.get("full_name", "")
            name_parts = full_name.split(" ", 1) if full_name else ["", ""]
            first_name = name_parts[0] if len(name_parts) > 0 else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # 1. Standard Fields (Direct Fill)
            for selector, val in [
                ("#first_name", first_name),
                ("#last_name", last_name),
                ("#email", candidate_data.get("email", "")),
                ("#phone", candidate_data.get("phone", ""))
            ]:
                if val and await page.query_selector(selector):
                    await browser_engine.direct_fill(page, selector, val)

            # 2. Upload Resume PDF
            if resume_pdf_path and os.path.exists(resume_pdf_path):
                file_input = await page.query_selector('input[type="file"][name*="resume" i], input[type="file"]')
                if file_input:
                    await file_input.set_input_files(resume_pdf_path)
                    logger.info(f"Attached resume file to Greenhouse: {resume_pdf_path}")

            # 3. Social / Portfolio Links
            links_map = [
                (["input[id*='linkedin' i]", "input[name*='linkedin' i]", "input[autocomplete*='linkedin' i]"], candidate_data.get("linkedin_url")),
                (["input[id*='github' i]", "input[name*='github' i]"], candidate_data.get("github_url")),
                (["input[id*='website' i]", "input[name*='website' i]", "input[id*='portfolio' i]"], candidate_data.get("portfolio_url"))
            ]
            for selectors, link_val in links_map:
                if link_val:
                    for sel in selectors:
                        el = await page.query_selector(sel)
                        if el:
                            await browser_engine.direct_fill(page, sel, link_val)
                            break

            # 4. Cover Letter Area
            if cover_letter:
                cl_selectors = ["#cover_letter_text", "textarea[name*='cover_letter' i]", "textarea[id*='cover_letter' i]"]
                for sel in cl_selectors:
                    el = await page.query_selector(sel)
                    if el:
                        await el.fill(cover_letter)
                        logger.info("Filled cover letter text area in Greenhouse.")
                        break

            # 5. Fill custom question textareas if answer exists
            if isinstance(form_answers, dict):
                answers_dict = form_answers.get("answers", form_answers)
                why_ans = answers_dict.get("why_this_company") or answers_dict.get("why_company")
                if why_ans:
                    custom_textareas = await page.query_selector_all("form textarea:not([name*='cover_letter' i])")
                    for ta in custom_textareas:
                        curr_val = await ta.input_value()
                        if not curr_val:
                            await ta.fill(why_ans)

            logger.info("Greenhouse form fields prefilled successfully.")
            return True
        except Exception as e:
            logger.error(f"Error filling Greenhouse form: {e}")
            return False

greenhouse_filler = GreenhouseFiller()
