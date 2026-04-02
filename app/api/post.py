from fastapi import APIRouter, HTTPException
from app.models.schemas import CreatePostRequest, CreatePostResponse
from app.services.post_service import create_post
from app.dependencies.session_manager import session_exists
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/create-post", tags=["Post"])


@router.post(
    "",
    response_model=CreatePostResponse,
    summary="Create a post in a subreddit",
    description="""
Create a text post in a subreddit using a stored browser session.

- Requires a prior successful call to `/create-account` (session file must exist)
- Title must be non-empty (validated by Pydantic + route-level check)
- Returns the live post URL and Reddit post ID on success
- Random delays are applied before submission to reduce spam detection risk
""",
)
async def create_post_endpoint(body: CreatePostRequest):
    if not body.title.strip():
        raise HTTPException(status_code=400, detail="Post title cannot be empty or whitespace.")
    if not session_exists(body.username):
        raise HTTPException(
            status_code=404,
            detail=f"No session found for '{body.username}'. Call /create-account first.",
        )
    sub = body.subreddit.lstrip("r/").strip()
    logger.info(f"POST /create-post → {body.username} → r/{sub}: {body.title[:50]!r}")
    result = await create_post(body.username, sub, body.title, body.content)
    return CreatePostResponse(**result)
