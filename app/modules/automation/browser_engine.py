import os
import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.config import settings

logger = logging.getLogger("BrowserEngine")

class BrowserEngine:
    def __init__(self):
        self.screenshot_dir = os.path.join(settings.STORAGE_DIR, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)

    async def create_browser_context(self, p, headless: bool = True) -> tuple[Browser, BrowserContext, Page]:
        """
        Creates a standard, functional Playwright Chromium browser context.
        Operates without anti-detection, stealth wrappers, or artificial delays.
        """
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1280,800"
            ]
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 800}
        )

        page = await context.new_page()
        return browser, context, page

    # Backward compatibility alias
    async def create_stealth_context(self, p, headless: bool = True) -> tuple[Browser, BrowserContext, Page]:
        return await self.create_browser_context(p, headless=headless)

    async def direct_fill(self, page: Page, selector: str, text: str):
        """Direct, functional field filling with no artificial typing delays."""
        if text is None or text == "":
            return
        try:
            el = await page.wait_for_selector(selector, timeout=3000)
            if el:
                await el.fill(str(text))
        except Exception as e:
            logger.debug(f"Direct fill skipped for selector {selector}: {e}")

    # Backward compatibility alias
    async def human_type(self, page: Page, selector: str, text: str, min_delay: int = 0, max_delay: int = 0):
        await self.direct_fill(page, selector, text)

    async def capture_screenshot(self, page: Page, application_id: str, name_prefix: str = "submitted") -> str:
        """Captures a full-page screenshot and returns the absolute file path."""
        screenshot_path = os.path.abspath(os.path.join(self.screenshot_dir, f"{application_id}_{name_prefix}.png"))
        try:
            await page.screenshot(path=screenshot_path, full_page=True)
            return screenshot_path
        except Exception as e:
            logger.warning(f"Failed to capture screenshot: {e}")
            return ""

browser_engine = BrowserEngine()
