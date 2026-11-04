from llmsharing.exceptions import TransientError


def retry(max_attempts: int = 3):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except TransientError:
                    if attempt == max_attempts:
                        raise
        return wrapper
    return decorator