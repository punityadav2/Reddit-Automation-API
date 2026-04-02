"""
Integration tests for all 3 API endpoints using FastAPI TestClient.
Playwright calls are mocked so no real browser is launched.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────────

def test_root_health():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


# ── POST /create-account ──────────────────────────────────────────────────────

@patch("app.api.account.create_reddit_account", new_callable=AsyncMock)
def test_create_account_success(mock_fn):
    mock_fn.return_value = {
        "success": True,
        "username": "testuser",
        "message": "Account created successfully",
    }
    resp = client.post("/create-account", json={
        "username": "testuser",
        "password": "Test@1234",
        "email": "test@example.com",
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert resp.json()["username"] == "testuser"


@patch("app.api.account.create_reddit_account", new_callable=AsyncMock)
def test_create_account_failure(mock_fn):
    mock_fn.return_value = {
        "success": False,
        "username": None,
        "message": "Username already taken",
    }
    resp = client.post("/create-account", json={
        "username": "testuser",
        "password": "Test@1234",
        "email": "test@example.com",
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is False


def test_create_account_invalid_payload():
    # username too short -> Pydantic 422
    resp = client.post("/create-account", json={
        "username": "ab",
        "password": "Test@1234",
        "email": "x@x.com",
    })
    assert resp.status_code == 422


# ── POST /join-subreddit ──────────────────────────────────────────────────────

@patch("app.api.subreddit.session_exists", return_value=False)
def test_join_subreddit_no_session(mock_exists):
    resp = client.post("/join-subreddit", json={"username": "nobody", "subreddit": "python"})
    assert resp.status_code == 404


@patch("app.api.subreddit.session_exists", return_value=True)
@patch("app.api.subreddit.join_subreddit", new_callable=AsyncMock)
def test_join_subreddit_success(mock_join, mock_exists):
    mock_join.return_value = {"joined": True, "subreddit": "python", "reason": "success"}
    resp = client.post("/join-subreddit", json={"username": "testuser", "subreddit": "r/python"})
    assert resp.status_code == 200
    assert resp.json()["joined"] is True


@patch("app.api.subreddit.session_exists", return_value=True)
@patch("app.api.subreddit.join_subreddit", new_callable=AsyncMock)
def test_join_private_subreddit(mock_join, mock_exists):
    mock_join.return_value = {"joined": False, "subreddit": "secret", "reason": "private"}
    resp = client.post("/join-subreddit", json={"username": "testuser", "subreddit": "secret"})
    assert resp.status_code == 200
    assert resp.json()["joined"] is False
    assert resp.json()["reason"] == "private"


# ── POST /create-post ─────────────────────────────────────────────────────────

def test_create_post_empty_title_rejected():
    # Pydantic min_length=1 rejects empty string
    resp = client.post("/create-post", json={
        "username": "testuser",
        "subreddit": "python",
        "title": "",
        "content": "Hello",
    })
    assert resp.status_code == 422


@patch("app.api.post.session_exists", return_value=False)
def test_create_post_no_session(mock_exists):
    resp = client.post("/create-post", json={
        "username": "nobody",
        "subreddit": "python",
        "title": "My Post",
        "content": "Content here",
    })
    assert resp.status_code == 404


@patch("app.api.post.session_exists", return_value=True)
@patch("app.api.post.create_post", new_callable=AsyncMock)
def test_create_post_success(mock_create, mock_exists):
    mock_create.return_value = {
        "success": True,
        "post_url": "https://www.reddit.com/r/python/comments/abc123/my_post/",
        "post_id": "abc123",
        "status": "posted",
    }
    resp = client.post("/create-post", json={
        "username": "testuser",
        "subreddit": "python",
        "title": "My Post",
        "content": "Hello Reddit!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["post_id"] == "abc123"
    assert "reddit.com" in data["post_url"]
