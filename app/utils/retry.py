"""
Retry utility — exponential backoff decorator for flaky operations.

Usage:
    from app.utils.retry import with_retry

    @with_retry
    async def some_flaky_operation():
        ...

Or with custom settings:
    @with_retry(max_retries=5, backoff=1.5)
    async def another_operation():
        ...
"""

import functools
from typing import Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from playwright.async_api import TimeoutError as PWTimeout

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def with_retry(func=None, *, max_retries: Optional[int] = None, backoff: Optional[float] = None):
    """
    Decorator that adds exponential backoff retries to async functions.

    Retries only on Playwright timeout and connection errors — not on
    validation or business-logic failures.

    Can be used bare or with arguments:
        @with_retry
        @with_retry(max_retries=5, backoff=1.5)
    """
    _max = max_retries or settings.max_retries
    _backoff = backoff or settings.retry_backoff

    def decorator(fn):
        @retry(
            stop=stop_after_attempt(_max),
            wait=wait_exponential(multiplier=_backoff, min=1, max=30),
            retry=retry_if_exception_type((PWTimeout, ConnectionError, OSError)),
            before_sleep=before_sleep_log(logger, log_level=20),  # INFO
            reraise=True,
        )
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            return await fn(*args, **kwargs)

        return wrapper

    if func is not None:  # bare @with_retry  (no parentheses)
        return decorator(func)
    return decorator  # @with_retry(max_retries=5)
