import asyncio
import functools

from llmsharing.exceptions import TransientError


def delay(attempt: int, base_delay: float = 0.1, factor: float = 2.0) -> float:
    """Seconds to wait after a failed attempt"""
    return base_delay * (factor ** (attempt - 1))


def retry(max_attempts: int = 3, base_delay: float = 0.1, factor: float = 2.0):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except TransientError:
                    if attempt == max_attempts:
                        raise
                    await asyncio.sleep(delay(attempt, base_delay, factor))
        return wrapper
    return decorator