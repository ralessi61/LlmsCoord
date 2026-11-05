import unittest
from unittest.mock import AsyncMock, patch
from unittest.mock import call as expected_call

from llmsharing.decorators import retry
from llmsharing.exceptions import AuthError, ProviderTimeoutError, RateLimitError


class TestRetry(unittest.IsolatedAsyncioTestCase):
    
    async def test_retries_transient_then_succeeds(self):
        """Retry once after a transient error and request the backoff without waiting.
        asyncio.sleep is mocked so the test is instantenous. One failed attempt
        must ask for delay(1), which is 0.1s, before the second call succeeds.
        """
        call = AsyncMock(side_effect=[RateLimitError(), "ok"])
        @retry(max_attempts=3)
        async def generate():
            return await call()
        # For the duration of that block, asyncio.sleep inside decorators.py does not really wait. 
        # A stand-in takes its place, records the arguments, and returns immediately.
        with patch("llmsharing.decorators.asyncio.sleep", new_callable=AsyncMock) as sleep:
            self.assertEqual(await generate(), "ok")
        self.assertEqual(call.call_count, 2)
        sleep.assert_awaited_once_with(0.1)


    async def test_does_not_retry_permanent_error(self):
        """A permanent error propagates on the first call, no backoff requested."""
        call = AsyncMock(side_effect=AuthError())
        @retry(max_attempts=3)
        async def generate():
            return await call()
        with (
            patch("llmsharing.decorators.asyncio.sleep", new_callable=AsyncMock) as sleep,
            self.assertRaises(AuthError),
        ):
            await generate()
        self.assertEqual(call.call_count, 1)
        self.assertEqual(sleep.await_count, 0)


    async def test_gives_up_after_max_attempts(self):
        """After max_attempts the error propagates. Backoff is requested between tries only."""
        call = AsyncMock(side_effect=ProviderTimeoutError())

        @retry(max_attempts=3)
        async def generate():
            return await call()

        with (
            patch("llmsharing.decorators.asyncio.sleep", new_callable=AsyncMock) as sleep,
            self.assertRaises(ProviderTimeoutError),
        ):
            await generate()
        self.assertEqual(call.call_count, 3)
        self.assertEqual(sleep.await_args_list, [expected_call(0.1), expected_call(0.2)])