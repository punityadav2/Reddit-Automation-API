"""
Subreddit Service — join a subreddit using a stored session.

Flow:
    1. Load session cookies for the given username
    2. Navigate to r/<subreddit>/
    3. Handle edge cases: private, not found, already joined
    4. Click the Join button and verify membership
    5. Persist updated cookies
"""

from playwright.async_api import TimeoutError as PWTimeout

from app.services.browser_service import get_browser_context
from app.dependencies.session_manager import load_session, save_session
from app.utils.delay import random_delay, scroll_randomly
from app.utils.logger import get_logger

logger = get_logger(__name__)

REDDIT_BASE = "https://www.reddit.com"


async def join_subreddit(username: str, subreddit: str) -> dict:
    """
    Join a Reddit subreddit using the stored session for `username`.

    Returns:
        dict with keys:
            joined    (bool)
            subreddit (str)
            reason    (str)  — "success" | "already_member" | "private" |
                               "not_found" | "no_session" | "join_button_not_found" |
                               "timeout" | error message
    """
    sub = subreddit.lstrip("r/").strip()

    cookies = load_session(username)
    if not cookies:
        return {"joined": False, "subreddit": sub, "reason": "no_session"}

    url = f"{REDDIT_BASE}/r/{sub}/"

    async with get_browser_context(cookies=cookies) as context:
        page = await context.new_page()
        try:
            logger.info(f"Navigating to {url}")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await random_delay(1.5, 3.0)

            # ── HTTP-level checks ──────────────────────────────────────────
            if response and response.status == 404:
                return {"joined": False, "subreddit": sub, "reason": "not_found"}
            if response and response.status == 403:
                return {"joined": False, "subreddit": sub, "reason": "private"}

            # ── DOM-level private check ────────────────────────────────────
            private_el = await page.query_selector(
                '[data-testid="subreddit-page--private"], '
                'h3:has-text("This community is private")'
            )
            if private_el:
                return {"joined": False, "subreddit": sub, "reason": "private"}

            await scroll_randomly(page, times=1)
            await random_delay(0.8, 1.5)

            # ── Already a member? ──────────────────────────────────────────
            joined_btn = await page.query_selector(
                'button:has-text("Joined"), button:has-text("Leave")'
            )
            if joined_btn:
                logger.info(f"Already a member of r/{sub}")
                return {"joined": True, "subreddit": sub, "reason": "already_member"}

            # ── Find Join button (new + old Reddit selectors) ──────────────
            join_btn = await page.query_selector(
                'button:has-text("Join"), '
                '.side .fancy-toggle-button .add, '
                '[data-testid="join-button"]'
            )
            if not join_btn:
                logger.warning(f"Join button not found for r/{sub}")
                return {"joined": False, "subreddit": sub, "reason": "join_button_not_found"}

            await join_btn.click()
            await random_delay(1.0, 2.0)

            # ── Verify success ─────────────────────────────────────────────
            verify_el = await page.query_selector(
                'button:has-text("Joined"), button:has-text("Leave")'
            )
            if verify_el:
                updated = await context.cookies()
                save_session(username, updated)
                logger.info(f"Joined r/{sub} ✓")
                return {"joined": True, "subreddit": sub, "reason": "success"}

            return {"joined": False, "subreddit": sub, "reason": "join_click_failed"}

        except PWTimeout as exc:
            logger.error(f"Timeout joining r/{sub}: {exc}")
            return {"joined": False, "subreddit": sub, "reason": "timeout"}
        except Exception as exc:
            logger.error(f"Error joining r/{sub}: {exc}", exc_info=True)
            return {"joined": False, "subreddit": sub, "reason": str(exc)}
        finally:
            await page.close()
