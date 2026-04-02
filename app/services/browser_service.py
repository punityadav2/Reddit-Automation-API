"""
Browser Service — Playwright browser/context factory.

Provides a single async context manager `get_browser_context()` that:
  - Launches headless Chromium
  - Applies stealth patches (removes webdriver fingerprint)
  - Rotates user-agent on every invocation
  - Optionally loads session cookies and configures a proxy
  - Guarantees cleanup (browser.close()) even on exceptions
"""

from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, List

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
)

from app.config.settings import settings
from app.utils.delay import random_user_agent
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Stealth init script — removes the most common bot fingerprints
_STEALTH_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    window.chrome = { runtime: {} };
"""


@asynccontextmanager
async def get_browser_context(
    cookies: Optional[List[dict]] = None,
    proxy_url: Optional[str] = None,
    headless: Optional[bool] = None,        # None → use settings.headless
) -> AsyncGenerator[BrowserContext, None]:
    """
    Async context manager that yields a configured Playwright BrowserContext.

    Args:
        cookies:    List of cookie dicts to inject (restores a saved session).
        proxy_url:  Overrides settings.proxy_url for this context only.
        headless:   Override headless mode. Pass False to show the browser window
                    (needed for manual CAPTCHA solving).

    Usage:
        async with get_browser_context(cookies=session_cookies) as context:
            page = await context.new_page()
            ...
    """
    effective_proxy = proxy_url or settings.proxy_url
    proxy = {"server": effective_proxy} if effective_proxy else None
    is_headless = settings.headless if headless is None else headless

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(
            headless=is_headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
            ],
        )

        context: BrowserContext = await browser.new_context(
            user_agent=random_user_agent(),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
            proxy=proxy,
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )

        # Apply stealth patches to every new page opened in this context
        await context.add_init_script(_STEALTH_SCRIPT)

        if cookies:
            await context.add_cookies(cookies)
            logger.info("Session cookies restored into browser context")

        try:
            yield context
        finally:
            await context.close()
            await browser.close()
            logger.info("Browser closed")
