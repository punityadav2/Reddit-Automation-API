"""
Session Manager — cookie persistence for browser sessions.

Each username gets a JSON file at data/sessions/<username>.json
containing the list of Playwright cookie dicts.

These are loaded back into a BrowserContext via get_browser_context(cookies=...)
to restore an authenticated Reddit session without re-logging in.
"""

import json
from pathlib import Path
from typing import Optional, List

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _session_path(username: str) -> Path:
    return Path(settings.session_dir) / f"{username}.json"


def save_session(username: str, cookies: List[dict]) -> None:
    """Persist browser cookies to disk for a given username."""
    path = _session_path(username)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2)
    logger.info(f"Session saved: {path}")


def load_session(username: str) -> Optional[List[dict]]:
    """Load cookies from disk. Returns None if no session file exists."""
    path = _session_path(username)
    if not path.exists():
        logger.warning(f"No session file for user: {username}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    logger.info(f"Session loaded: {path}")
    return cookies


def session_exists(username: str) -> bool:
    """Check whether a session file exists for this username."""
    return _session_path(username).exists()


def delete_session(username: str) -> None:
    """Remove a session file (e.g. after logout or expiry)."""
    path = _session_path(username)
    if path.exists():
        path.unlink()
        logger.info(f"Session deleted: {path}")
