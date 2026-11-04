class CoordinatorError(Exception):
    """ Base exception """
    def __init__(self, message: str, status_code: int | None = None, is_retryable: bool = False) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.is_retryable = is_retryable


class TransientError(CoordinatorError):
    """ for transient errors """
    def __init__(self, message: str, status_code: int | None = None, cause: str | None = None) -> None:
        super().__init__(message, status_code=status_code, is_retryable=True)
        self.cause = cause


class RateLimitError(TransientError):
    """ for rate limit errors """
    def __init__(self, message: str = "Rate limit exceeded", retry_after: float | None = None) -> None:
        super().__init__(message, status_code=429  )
        self.retry_after = retry_after # cannot be passed to TransientError, it is an attribute of this class only


class ProviderTimeoutError(TransientError):
    """ for provider timeout """
    def __init__(self, message: str = "Provider timeout", timeout: float | None = None) -> None:
        super().__init__(message, status_code=504)
        self.timeout = timeout


class ServerUnavailableProviderError(TransientError):
    """ server unavailable provider errors """
    def __init__(self, message: str = "Server unavailable provider", cause: str | None = None) -> None:
        super().__init__(message, status_code=503)
        self.cause = cause


class PermanentError(CoordinatorError):
    """ permanent errors """
    def __init__(self, message: str, status_code: int | None = None, cause: str | None = None) -> None:
        super().__init__(message, status_code=status_code)
        self.cause = cause


class InvalidRequestError(PermanentError):
    """ invalid requests """
    def __init__(self, message: str = "Invalid request error", cause: str | None = None) -> None:
        super().__init__(message, status_code=400)
        self.cause = cause


class ProviderNotFoundError(PermanentError):
    """ LLM provider not registered """
    def __init__(self, message: str = "Provider unknown", cause: str | None = None) -> None:
        super().__init__(message, status_code=404)
        self.cause = cause


class AuthError(PermanentError):    
    """ Auth invalid """
    def __init__(self, message: str = "Auth failed", cause: str | None = None) -> None:
        super().__init__(message, status_code=401) #work done from father class PermanentError
        self.cause = cause   
