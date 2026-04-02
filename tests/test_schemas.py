import pytest
from pydantic import ValidationError
from app.models.schemas import (
    CreateAccountRequest,
    JoinSubredditRequest,
    CreatePostRequest,
)


# ── CreateAccountRequest ──────────────────────────────────────────────────────

def test_create_account_valid():
    req = CreateAccountRequest(username="testuser", password="Test@1234", email="test@example.com")
    assert req.username == "testuser"
    assert req.email == "test@example.com"


def test_create_account_username_too_short():
    with pytest.raises(ValidationError):
        CreateAccountRequest(username="ab", password="Test@1234", email="test@example.com")


def test_create_account_password_too_short():
    with pytest.raises(ValidationError):
        CreateAccountRequest(username="testuser", password="short", email="test@example.com")


# ── JoinSubredditRequest ──────────────────────────────────────────────────────

def test_join_subreddit_valid():
    req = JoinSubredditRequest(username="testuser", subreddit="r/python")
    assert req.subreddit == "r/python"


# ── CreatePostRequest ─────────────────────────────────────────────────────────

def test_create_post_valid():
    req = CreatePostRequest(username="testuser", subreddit="python", title="Hello", content="World")
    assert req.title == "Hello"
    assert req.content == "World"


def test_create_post_default_content():
    # content is optional, defaults to ""
    req = CreatePostRequest(username="testuser", subreddit="python", title="Hello")
    assert req.content == ""


def test_create_post_empty_title_fails():
    with pytest.raises(ValidationError):
        CreatePostRequest(username="testuser", subreddit="python", title="")
