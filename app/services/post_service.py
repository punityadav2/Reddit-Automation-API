"""
Post Service — create a text post in a subreddit using a stored session.

Flow:
    1. Load session cookies for `username`
    2. Navigate to r/<subreddit>/submit
    3. Select "Text" post type
    4. Fill title and body with human-like delays
    5. Submit and extract post URL/ID from the redirect
    6. Persist updated cookies
"""

import re
from playwright.async_api import TimeoutError as PWTimeout

from app.services.browser_service import get_browser_context
from app.dependencies.session_manager import load_session, save_session
from app.utils.delay import human_type, random_delay, scroll_randomly
from app.utils.logger import get_logger

logger = get_logger(__name__)

REDDIT_BASE = "https://www.reddit.com"


async def create_post(
    username: str,
    subreddit: str,
    title: str,
    content: str,
) -> dict:
    """
    Create a text post in a subreddit.

    Returns:
        dict with keys:
            success  (bool)
            post_url (str | None)
            post_id  (str | None)
            status   (str)  — "posted" | "no_session" | "subreddit_not_found" |
                              "forbidden" | "submit_button_not_found" | "timeout" | error
    """
    sub = subreddit.lstrip("r/").strip()

    cookies = load_session(username)
    if not cookies:
        return {"success": False, "post_url": None, "post_id": None, "status": "no_session"}

    submit_url = f"{REDDIT_BASE}/r/{sub}/submit"

    async with get_browser_context(cookies=cookies) as context:
        page = await context.new_page()
        try:
            logger.info(f"Navigating to {submit_url}")
            response = await page.goto(submit_url, wait_until="domcontentloaded", timeout=30_000)
            await random_delay(1.5, 3.0)

            # ── HTTP-level checks ──────────────────────────────────────────
            if response and response.status == 404:
                return {"success": False, "post_url": None, "post_id": None, "status": "subreddit_not_found"}
            if response and response.status == 403:
                return {"success": False, "post_url": None, "post_id": None, "status": "forbidden"}

            # ── Select "Text" post type (if tabs are shown) ────────────────
            text_tab = await page.query_selector(
                'button:has-text("Text"), '
                '[data-testid="post-type-link-text"], '
                '.tab-nav button:nth-child(2)'
            )
            if text_tab:
                await text_tab.click()
                await random_delay(0.5, 1.0)

            # ── Fill title ─────────────────────────────────────────────────
            title_sel = (
                'textarea[placeholder*="Title"], '
                'input[name="title"], '
                '[data-testid="post-title-field"] textarea, '
                '#title-textarea'
            )
            await page.wait_for_selector(title_sel, timeout=10_000)
            await human_type(page, title_sel, title)
            await random_delay(0.5, 1.5)

            # ── Fill body ──────────────────────────────────────────────────
            if content:
                body_sel = (
                    '.public-DraftEditor-content, '
                    '[data-testid="post-body-field"] div[contenteditable], '
                    'textarea[name="text"], '
                    '#text-body-textarea'
                )
                body_el = await page.query_selector(body_sel)
                if body_el:
                    await body_el.click()
                    await page.keyboard.type(content)
                    await random_delay(0.8, 1.5)

            await scroll_randomly(page, times=1)
            await random_delay(1.0, 2.0)

            # ── Submit ─────────────────────────────────────────────────────
            submit_btn = await page.query_selector(
                '[data-testid="post-submit-button"], '
                'button:has-text("Post"), '
                'button[type="submit"]:has-text("Submit")'
            )
            if not submit_btn:
                return {
                    "success": False,
                    "post_url": None,
                    "post_id": None,
                    "status": "submit_button_not_found",
                }

            await submit_btn.click()
            logger.info("Post submitted — waiting for redirect...")

            # ── Wait for redirect to the new post ──────────────────────────
            await page.wait_for_url(
                re.compile(r"reddit\.com/r/.+/comments/"),
                timeout=15_000,
            )
            post_url = page.url

            # Extract post ID (e.g. /comments/abc123/)
            match = re.search(r"/comments/([a-z0-9]+)/", post_url)
            post_id = match.group(1) if match else None

            # Persist refreshed session cookies
            updated = await context.cookies()
            save_session(username, updated)

            logger.info(f"Post created ✓ — {post_url}")
            return {
                "success": True,
                "post_url": post_url,
                "post_id": post_id,
                "status": "posted",
            }

        except PWTimeout as exc:
            logger.error(f"Timeout creating post: {exc}")
            return {"success": False, "post_url": None, "post_id": None, "status": "timeout"}
        except Exception as exc:
            logger.error(f"Error creating post: {exc}", exc_info=True)
            return {"success": False, "post_url": None, "post_id": None, "status": str(exc)}
        finally:
            await page.close()
