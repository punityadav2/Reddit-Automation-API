"""
Human-like delay and typing utilities.

These make Playwright interactions harder to fingerprint as bot traffic
by adding per-character typing delays, random sleep intervals, and
simulated scroll behaviour.
"""

import asyncio
import random
from typing import Optional


async def random_delay(min_sec: float = 1.0, max_sec: float = 3.0) -> None:
    """Sleep for a uniformly random duration."""
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def human_type(page, selector: str, text: str,
                     min_ms: int = 50, max_ms: int = 180) -> None:
    """
    Type text into a field one character at a time with jittered delays.
    Much harder to distinguish from real typing than page.fill().
    """
    await page.click(selector)
    await asyncio.sleep(random.uniform(0.2, 0.5))
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)


async def scroll_randomly(page, times: int = 2) -> None:
    """Scroll the viewport in small increments to simulate reading."""
    for _ in range(times):
        px = random.randint(150, 500)
        await page.mouse.wheel(0, px)
        await random_delay(0.4, 1.2)


def random_user_agent() -> str:
    """Return a realistic Chrome user-agent string."""
    versions = ["122.0.0.0", "123.0.0.0", "124.0.0.0", "125.0.0.0"]
    platforms = [
        "Windows NT 10.0; Win64; x64",
        "Macintosh; Intel Mac OS X 10_15_7",
        "X11; Linux x86_64",
    ]
    v = random.choice(versions)
    p = random.choice(platforms)
    return (
        f"Mozilla/5.0 ({p}) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{v} Safari/537.36"
    )
