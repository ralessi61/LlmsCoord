

def retry(max_attempts: int = 3):
    """func internal called once"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator