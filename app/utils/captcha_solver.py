"""
CAPTCHA Solver — hCaptcha integration for Reddit signup.

Reddit's registration page uses hCaptcha. This module handles solving it via:
  1. 2captcha (https://2captcha.com) — set CAPTCHA_SERVICE=2captcha
  2. Anti-Captcha (https://anti-captcha.com) — set CAPTCHA_SERVICE=anticaptcha

If CAPTCHA_API_KEY is not set, the module logs a warning and returns None.
In that case, account creation will likely fail at the CAPTCHA step (expected
behavior in dev/test environments without a paid CAPTCHA service).

Usage:
    token = await solve_hcaptcha(site_key, page_url)
    if token:
        await inject_captcha_token(page, token)
"""

import asyncio
import httpx
from typing import Optional

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_TWOCAPTCHA_SUBMIT = "https://2captcha.com/in.php"
_TWOCAPTCHA_RESULT = "https://2captcha.com/res.php"
_ANTICAPTCHA_URL = "https://api.anti-captcha.com"


async def solve_hcaptcha(site_key: str, page_url: str) -> Optional[str]:
    """
    Solve an hCaptcha challenge and return the response token.
    Returns None if no CAPTCHA_API_KEY is configured.
    """
    if not settings.captcha_api_key:
        logger.warning(
            "CAPTCHA_API_KEY not set — skipping CAPTCHA solve. "
            "Account creation may fail at the CAPTCHA step."
        )
        return None

    logger.info(f"Solving hCaptcha via {settings.captcha_service} for: {page_url}")

    if settings.captcha_service == "2captcha":
        return await _solve_2captcha(site_key, page_url)
    elif settings.captcha_service == "anticaptcha":
        return await _solve_anticaptcha(site_key, page_url)
    else:
        logger.error(f"Unknown CAPTCHA service: {settings.captcha_service}")
        return None


async def _solve_2captcha(site_key: str, page_url: str) -> Optional[str]:
    async with httpx.AsyncClient(timeout=120) as client:
        # Submit task
        resp = await client.post(_TWOCAPTCHA_SUBMIT, data={
            "key": settings.captcha_api_key,
            "method": "hcaptcha",
            "sitekey": site_key,
            "pageurl": page_url,
            "json": 1,
        })
        data = resp.json()
        if data.get("status") != 1:
            logger.error(f"2captcha submit failed: {data}")
            return None

        task_id = data["request"]
        logger.info(f"2captcha task submitted (id={task_id}), polling...")

        # Poll up to 2.5 minutes
        for _ in range(30):
            await asyncio.sleep(5)
            res = await client.get(_TWOCAPTCHA_RESULT, params={
                "key": settings.captcha_api_key,
                "action": "get",
                "id": task_id,
                "json": 1,
            })
            result = res.json()
            if result.get("status") == 1:
                logger.info("2captcha: solved ✓")
                return result["request"]
            if result.get("request") != "CAPCHA_NOT_READY":
                logger.error(f"2captcha error: {result}")
                return None

        logger.error("2captcha: timed out after 150s")
        return None


async def _solve_anticaptcha(site_key: str, page_url: str) -> Optional[str]:
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{_ANTICAPTCHA_URL}/createTask", json={
            "clientKey": settings.captcha_api_key,
            "task": {
                "type": "HCaptchaTaskProxyless",
                "websiteURL": page_url,
                "websiteKey": site_key,
            },
        })
        data = resp.json()
        if data.get("errorId") != 0:
            logger.error(f"Anti-Captcha createTask failed: {data}")
            return None

        task_id = data["taskId"]
        logger.info(f"Anti-Captcha task created (id={task_id}), polling...")

        for _ in range(30):
            await asyncio.sleep(5)
            res = await client.post(f"{_ANTICAPTCHA_URL}/getTaskResult", json={
                "clientKey": settings.captcha_api_key,
                "taskId": task_id,
            })
            result = res.json()
            if result.get("status") == "ready":
                logger.info("Anti-Captcha: solved ✓")
                return result["solution"]["gRecaptchaResponse"]
            if result.get("errorId") != 0:
                logger.error(f"Anti-Captcha error: {result}")
                return None

        logger.error("Anti-Captcha: timed out after 150s")
        return None


async def inject_captcha_token(page, token: str) -> None:
    """Inject the solved hCaptcha token directly into the page DOM."""
    await page.evaluate(f"""
        (() => {{
            const el = document.querySelector('[name="h-captcha-response"]');
            const el2 = document.querySelector('[name="g-recaptcha-response"]');
            if (el) el.value = '{token}';
            if (el2) el2.value = '{token}';
        }})();
    """)
    logger.info("CAPTCHA token injected into page")
