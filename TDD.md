## TDD notes ##
Only on retry decorator. unittest, IsolatedAsyncioTestCase.

RED  4fd86fa  three tests, decorator called through once, AssertionError
GREEN 0b84120 loop on TransientError, max_attempts, no backoff yet
GRAY  699fa86 delay() extracted, asyncio.sleep mocked

Retryable = TransientError. AuthError is permanent, so one attempt only.