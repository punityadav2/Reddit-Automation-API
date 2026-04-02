from pydantic import BaseModel, Field
from typing import Optional


# ─── Request Models ───────────────────────────────────────────────────────────

class CreateAccountRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="Reddit username (3-20 chars)")
    password: str = Field(..., min_length=8, description="Account password (min 8 chars)")
    email: str = Field(..., description="Valid email address")


class JoinSubredditRequest(BaseModel):
    username: str = Field(..., description="Reddit username whose session to use")
    subreddit: str = Field(..., description="Subreddit name (e.g. 'python' or 'r/python')")


class CreatePostRequest(BaseModel):
    username: str = Field(..., description="Reddit username whose session to use")
    subreddit: str = Field(..., description="Target subreddit name")
    title: str = Field(..., min_length=1, max_length=300, description="Post title")
    content: str = Field(default="", description="Post body text (optional)")


# ─── Response Models ───────────────────────────────────────────────────────────

class CreateAccountResponse(BaseModel):
    success: bool
    username: Optional[str] = None
    message: str


class JoinSubredditResponse(BaseModel):
    joined: bool
    subreddit: str
    reason: str  # "success" | "already_member" | "private" | "not_found" | "no_session" | "error"


class CreatePostResponse(BaseModel):
    success: bool
    post_url: Optional[str] = None
    post_id: Optional[str] = None
    status: str  # "posted" | "no_session" | "subreddit_not_found" | "timeout" | error msg
