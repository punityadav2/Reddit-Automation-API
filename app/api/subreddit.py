from fastapi import APIRouter, HTTPException
from app.models.schemas import JoinSubredditRequest, JoinSubredditResponse
from app.services.subreddit_service import join_subreddit
from app.dependencies.session_manager import session_exists
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/join-subreddit", tags=["Subreddit"])


@router.post(
    "",
    response_model=JoinSubredditResponse,
    summary="Join a subreddit",
    description="""
Join a subreddit using a stored browser session.

- Requires a prior successful call to `/create-account` (session file must exist)
- Handles private/restricted subreddits — returns `joined: false` with reason
- Returns `reason: "already_member"` if the user is already subscribed
- Accepts subreddit names with or without the `r/` prefix
""",
)
async def join_subreddit_endpoint(body: JoinSubredditRequest):
    if not session_exists(body.username):
        raise HTTPException(
            status_code=404,
            detail=f"No session found for '{body.username}'. Call /create-account first.",
        )
    sub = body.subreddit.lstrip("r/").strip()
    logger.info(f"POST /join-subreddit → {body.username} → r/{sub}")
    result = await join_subreddit(body.username, sub)
    return JoinSubredditResponse(**result)
