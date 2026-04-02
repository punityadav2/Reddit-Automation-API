"""
Auth Service — Reddit account creation automation via Playwright.

CAPTCHA Handling modes:
  1. API mode  — CAPTCHA_API_KEY is set → solved automatically via 2captcha/Anti-Captcha
  2. Manual mode — no API key + ALLOW_MANUAL_CAPTCHA=true (default) →
       Browser opens visibly, fills the form, then WAITS for you to solve
       the CAPTCHA yourself in the browser window and click Submit.
       Times out after MANUAL_CAPTCHA_TIMEOUT seconds (default 120).
  3. Headless skip — no API key + ALLOW_MANUAL_CAPTCHA=false →
       Logs a warning, submits without solving (will fail at CAPTCHA step).

Flow:
    1. Navigate to https://www.reddit.com/register/
    2. Fill email → click Continue
    3. Fill username + password (human-like typing)
    4. Solve hCaptcha (API, manual, or skip)
    5. Submit registration form
    6. Detect success → save session cookies
"""

import asyncio
from playwright.async_api import TimeoutError as PWTimeout

from app.services.browser_service import get_browser_context
from app.dependencies.session_manager import save_session
from app.utils.delay import human_type, random_delay
from app.utils.captcha_solver import solve_hcaptcha, inject_captcha_token
from app.utils.logger import get_logger
from app.config.settings import settings

logger = get_logger(__name__)

REGISTER_URL = "https://www.reddit.com/register/"
_REDDIT_HCAPTCHA_SITEKEY = "6LeTnxkTAAAAAN9QEuDZRpn90WwKk_R1TRW_g-JC"


async def _wait_for_manual_captcha(page, timeout: int) -> bool:
    """
    Wait for the user to solve CAPTCHA manually in a visible browser window.

    Prints clear instructions to the terminal, then polls the page URL
    every second until it changes away from /register/ (success) or times out.

    Returns True if the user completed registration, False on timeout.
    """
    print("\n" + "=" * 60)
    print("🧩  MANUAL CAPTCHA REQUIRED")
    print("=" * 60)
    print("A browser window has opened with the Reddit signup form.")
    print("The form has been filled in for you.")
    print("")
    print("👉  Please:")
    print("    1. Solve the CAPTCHA in the browser window")
    print("    2. Click the 'Sign Up' / 'Submit' button yourself")
    print(f"\n⏳  Waiting up to {timeout} seconds for you to complete it...")
    print("=" * 60 + "\n")

    for elapsed in range(timeout):
        await asyncio.sleep(1)
        current_url = page.url
        if "register" not in current_url and "reddit.com" in current_url:
            print("✅  Registration detected as successful!\n")
            return True
        if elapsed > 0 and elapsed % 30 == 0:
            remaining = timeout - elapsed
            print(f"⏳  Still waiting... {remaining}s remaining. Solve the CAPTCHA in the browser.")

    print(f"❌  Timed out after {timeout}s. No successful registration detected.\n")
    return False


async def create_reddit_account(username: str, password: str, email: str) -> dict:
    """
    Automate Reddit account creation.

    Returns:
        dict with keys:
            success  (bool)
            username (str | None)
            message  (str)
    """
    # ── Determine CAPTCHA mode ──────────────────────────────────────────────
    use_manual = (not settings.captcha_api_key) and settings.allow_manual_captcha
    # Manual mode needs a visible browser
    headless_override = False if use_manual else None

    if use_manual:
        logger.info(
            "No CAPTCHA_API_KEY set. Running in MANUAL CAPTCHA mode — "
            "browser will open visibly."
        )
    elif not settings.captcha_api_key:
        logger.warning(
            "No CAPTCHA_API_KEY and ALLOW_MANUAL_CAPTCHA=false. "
            "Proceeding headless — CAPTCHA step will likely fail."
        )

    async with get_browser_context(headless=headless_override) as context:
        page = await context.new_page()
        try:
            logger.info(f"Starting account creation for: {username}")
            await page.goto(REGISTER_URL, wait_until="networkidle", timeout=30_000)
            await random_delay(1.0, 2.0)

            # ── Step 1: Email ──────────────────────────────────────────────
            email_sel = 'input[id="regEmail"], input[name="email"], input[type="email"]'
            await page.wait_for_selector(email_sel, timeout=10_000)
            await human_type(page, email_sel, email)
            await random_delay(0.5, 1.0)

            continue_btn = await page.query_selector('button[type="submit"]')
            if continue_btn:
                await continue_btn.click()
            await random_delay(1.5, 2.5)

            # ── Step 2: Username ───────────────────────────────────────────
            user_sel = 'input[id="regUsername"], input[name="username"]'
            await page.wait_for_selector(user_sel, timeout=10_000)
            await human_type(page, user_sel, username)
            await random_delay(0.5, 1.0)

            # ── Step 3: Password ───────────────────────────────────────────
            pass_sel = 'input[id="regPassword"], input[name="password"], input[type="password"]'
            await human_type(page, pass_sel, password)
            await random_delay(0.5, 1.0)

            # ── Step 4: CAPTCHA ────────────────────────────────────────────
            if use_manual:
                # Hand off to user — wait for them to solve & submit
                success = await _wait_for_manual_captcha(page, settings.manual_captcha_timeout)
                if not success:
                    return {
                        "success": False,
                        "username": None,
                        "message": (
                            f"Manual CAPTCHA timed out after {settings.manual_captcha_timeout}s. "
                            "Please solve the CAPTCHA faster or increase MANUAL_CAPTCHA_TIMEOUT."
                        ),
                    }
            else:
                # API-based CAPTCHA solving
                token = await solve_hcaptcha(_REDDIT_HCAPTCHA_SITEKEY, REGISTER_URL)
                if token:
                    await inject_captcha_token(page, token)
                    await random_delay(0.5, 1.0)

                # Submit (only needed in API mode; manual mode user clicks Submit themselves)
                submit_btn = await page.query_selector('button[type="submit"]')
                if submit_btn:
                    await submit_btn.click()
                await random_delay(2.5, 4.0)

            # ── Step 5: Detect result ──────────────────────────────────────
            current_url = page.url
            if "register" not in current_url and "reddit.com" in current_url:
                cookies = await context.cookies()
                save_session(username, cookies)
                logger.info(f"Account created successfully: {username}")
                return {
                    "success": True,
                    "username": username,
                    "message": "Account created successfully",
                }

            # Check for inline error message
            error_el = await page.query_selector(
                '[data-testid="regflow-error"], '
                '.AnimatedForm__errorMessage, '
                '.errorMessage'
            )
            if error_el:
                error_text = (await error_el.inner_text()).strip()
                logger.warning(f"Registration error: {error_text}")
                return {"success": False, "username": None, "message": error_text}

            return {
                "success": False,
                "username": None,
                "message": "Registration did not complete. Check the browser window for details.",
            }

        except PWTimeout as exc:
            logger.error(f"Timeout during account creation: {exc}")
            return {"success": False, "username": None, "message": "Timeout during registration flow"}
        except Exception as exc:
            logger.error(f"Unexpected error during account creation: {exc}", exc_info=True)
            return {"success": False, "username": None, "message": str(exc)}
        finally:
            await page.close()
