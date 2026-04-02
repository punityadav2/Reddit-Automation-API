import pytest
import asyncio
import time
from app.utils.delay import random_delay, random_user_agent


@pytest.mark.asyncio
async def test_random_delay_within_range():
    start = time.perf_counter()
    await random_delay(0.1, 0.3)
    elapsed = time.perf_counter() - start
    # Allow generous upper bound for CI latency
    assert 0.08 <= elapsed <= 0.6


def test_random_user_agent_contains_chrome():
    ua = random_user_agent()
    assert "Mozilla" in ua
    assert "Chrome" in ua
    assert "Safari" in ua


def test_random_user_agent_varies():
    """Verify that UAs are rotated (not always the same string)."""
    agents = {random_user_agent() for _ in range(20)}
    assert len(agents) > 1  # should get at least 2 distinct UAs
