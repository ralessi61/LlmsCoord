import unittest
from unittest.mock import AsyncMock

from llmsharing.decorators import retry
from llmsharing.exceptions import AuthError, ProviderTimeoutError, RateLimitError


class TestRetry(unittest.IsolatedAsyncioTestCase):
    
    async def test_retries_transient_then_succeeds(self):
        call = AsyncMock(side_effect=[RateLimitError(), "ok"])
        @retry(max_attempts=3)
        async def generate():
            return await call()
        self.assertEqual(await generate(), "ok")
        self.assertEqual(call.call_count, 2)


    async def test_does_not_retry_permanent_error(self):
        call = AsyncMock(side_effect=AuthError())
        @retry(max_attempts=3)
        async def generate():
            return await call()
        with self.assertRaises(AuthError):
            await generate()
        self.assertEqual(call.call_count, 1)


    async def test_gives_up_after_max_attempts(self):
        call = AsyncMock(side_effect=ProviderTimeoutError())
        @retry(max_attempts=3)
        async def generate():
            return await call()
        with self.assertRaises(ProviderTimeoutError):
            await generate()
        self.assertEqual(call.call_count, 3)