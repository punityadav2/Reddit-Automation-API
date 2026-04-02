import pytest
import json
from unittest.mock import patch
from app.dependencies.session_manager import (
    save_session,
    load_session,
    session_exists,
    delete_session,
)

MOCK_COOKIES = [{"name": "token", "value": "abc123", "domain": ".reddit.com"}]


def test_save_and_load_session(tmp_path):
    with patch("app.dependencies.session_manager.settings") as mock_settings:
        mock_settings.session_dir = str(tmp_path)
        save_session("testuser", MOCK_COOKIES)
        loaded = load_session("testuser")
        assert loaded == MOCK_COOKIES


def test_session_exists_false_initially(tmp_path):
    with patch("app.dependencies.session_manager.settings") as mock_settings:
        mock_settings.session_dir = str(tmp_path)
        assert not session_exists("nobody")


def test_session_exists_true_after_save(tmp_path):
    with patch("app.dependencies.session_manager.settings") as mock_settings:
        mock_settings.session_dir = str(tmp_path)
        save_session("testuser", MOCK_COOKIES)
        assert session_exists("testuser")


def test_delete_session(tmp_path):
    with patch("app.dependencies.session_manager.settings") as mock_settings:
        mock_settings.session_dir = str(tmp_path)
        save_session("testuser", MOCK_COOKIES)
        delete_session("testuser")
        assert not session_exists("testuser")


def test_load_nonexistent_session(tmp_path):
    with patch("app.dependencies.session_manager.settings") as mock_settings:
        mock_settings.session_dir = str(tmp_path)
        result = load_session("nobody")
        assert result is None
