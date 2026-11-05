import asyncio
import contextvars
import functools
import logging
import time

from llmsharing.exceptions import TransientError

_retries = contextvars.ContextVar("retries", default=0)

def get_retry_count() -> int:
    return _retries.get()

logger = logging.getLogger(__name__)

def delay(attempt: int, base_delay: float = 0.1, factor: float = 2.0) -> float:
    """Seconds to wait after a failed attempt. attempt 1 -> 0.1s, 2 -> 0.2s."""
    return base_delay * (factor ** (attempt - 1))


def retry(max_attempts: int = 3, base_delay: float = 0.1, factor: float = 2.0):
    """Retry TransientError only; AuthError and the rest propagate.
    asyncio.sleep, not time.sleep, or event loop blocks.
    No sleep after the last attempt: already gone.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    _retries.set(attempt - 1)  # 0 if passed first hit
                    return result
                except TransientError:
                    if attempt == max_attempts:
                        _retries.set(attempt - 1)
                        raise
                    await asyncio.sleep(delay(attempt, base_delay, factor))
        return wrapper
    return decorator


def measure_execution_time(func):
    """
    time of one await. Must await, otherwise you time ~0s and the call never runs.
    Duration not logged if func raises (timer sits after the await).
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        logger.debug(f"function {func.__name__} took {(end - start):.2f} seconds")
        return result
    return wrapper


def call_counter(func):
    """
    numcalls lives on the wrapper, so concurrent tasks share one counter.
    OK as a total, not as retries of single request.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        wrapper.numcalls += 1
        logger.debug(f"Func called {wrapper.numcalls} times")
        return await func(*args, **kwargs)
    wrapper.numcalls = 0
    return wrapper
