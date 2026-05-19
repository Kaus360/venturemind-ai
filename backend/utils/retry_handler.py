from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any


logger = logging.getLogger(__name__)


async def retry_async(
    func: Callable[[], Awaitable[Any]],
    max_retries: int = 3,
    delay: float = 1.0,
    fallback: Any = None,
) -> Any:
    last_exception: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return await func()
        except Exception as exc:
            last_exception = exc
            logger.warning("Retry attempt %s failed: %s", attempt, exc)

            if attempt < max_retries:
                await asyncio.sleep(delay)

    if fallback is not None:
        return fallback

    if last_exception is not None:
        raise last_exception

    raise RuntimeError("retry_async failed without capturing an exception.")
