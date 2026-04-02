from fastapi import APIRouter, HTTPException
from app.models.schemas import CreateAccountRequest, CreateAccountResponse
from app.services.auth_service import create_reddit_account
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/create-account", tags=["Account"])


@router.post(
    "",
    response_model=CreateAccountResponse,
    summary="Create a Reddit account",
    description="""
Automate Reddit account registration using Playwright.

- Fills the signup form with the provided credentials (email, username, password)
- Saves session cookies to disk on success (used by the other endpoints)

**CAPTCHA Handling (two modes):**

1. **Manual mode (default)** — No API key needed. The browser opens **visibly** with the
   form pre-filled. You solve the CAPTCHA yourself and click Submit. The API waits up to
   `MANUAL_CAPTCHA_TIMEOUT` seconds (default: 120) for you to complete it.

2. **API mode** — Set `CAPTCHA_API_KEY` in `.env`. The CAPTCHA is solved automatically
   via 2captcha or Anti-Captcha (paid service). Browser stays headless.

Set `ALLOW_MANUAL_CAPTCHA=false` in `.env` to disable manual mode.
""",
)
async def create_account(body: CreateAccountRequest):
    logger.info(f"POST /create-account → username={body.username}")
    result = await create_reddit_account(body.username, body.password, body.email)
    return CreateAccountResponse(**result)
