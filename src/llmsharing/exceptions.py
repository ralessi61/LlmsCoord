class CoordinatorError(Exception):
    """Base exception for all coordinator-level failures."""
    def __init__(self, message: str, status_code: int | None = None, is_retryable: bool = False) -> None:
        """Store the message and any HTTP-like status metadata for the error."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.is_retryable = is_retryable


class TransientError(CoordinatorError):
    """Raised when a request may succeed if retried after a short delay."""
    def __init__(self, message: str, status_code: int | None = None, cause: str | None = None) -> None:
        """Mark the failure as retryable and keep an optional cause string."""
        super().__init__(message, status_code=status_code, is_retryable=True)
        self.cause = cause


class RateLimitError(TransientError):
    """Raised when the provider rejects requests because of rate limits."""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: float | None = None) -> None:
        """Create a rate-limit error with the recommended retry delay, if known."""
        super().__init__(message, status_code=429  )
        self.retry_after = retry_after # cannot be passed to TransientError, it is an attribute of this class only


class ProviderTimeoutError(TransientError):
    """Raised when a provider takes too long to answer."""
    def __init__(self, message: str = "Provider timeout", timeout: float | None = None) -> None:
        """Store the timeout value reported by the provider, if available."""
        super().__init__(message, status_code=504)
        self.timeout = timeout


class ServerUnavailableProviderError(TransientError):
    """Raised when the upstream provider is temporarily unavailable."""
    def __init__(self, message: str = "Server unavailable provider", cause: str | None = None) -> None:
        """Keep the original failure cause alongside the retryable status."""
        super().__init__(message, status_code=503)
        self.cause = cause


class PermanentError(CoordinatorError):
    """Raised when the request is invalid and should not be retried."""
    def __init__(self, message: str, status_code: int | None = None, cause: str | None = None) -> None:
        """Record the permanent failure and any related cause."""
        super().__init__(message, status_code=status_code)
        self.cause = cause


class InvalidRequestError(PermanentError):
    """Raised when the input payload is malformed or invalid."""
    def __init__(self, message: str = "Invalid request error", cause: str | None = None) -> None:
        """Set the standard 400 error metadata for invalid requests."""
        super().__init__(message, status_code=400)
        self.cause = cause


class ProviderNotFoundError(PermanentError):
    """Raised when a requested provider is not registered in the system."""
    def __init__(self, message: str = "Provider unknown", cause: str | None = None) -> None:
        """Hold the provider lookup failure details."""
        super().__init__(message, status_code=404)
        self.cause = cause


class AuthError(PermanentError):
    """Raised when authentication is missing or invalid."""
    def __init__(self, message: str = "Auth failed", cause: str | None = None) -> None:
        """Attach the standard 401 metadata for authentication failures."""
        super().__init__(message, status_code=401) #work done from father class PermanentError
        self.cause = cause
