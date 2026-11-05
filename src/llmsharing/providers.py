import asyncio
import random
from typing import ClassVar

from llmsharing.exceptions import ProviderTimeoutError, RateLimitError
from llmsharing.models import LLMRequest


class ProviderMeta(type):
    """Metaclass to register provider classes."""
    registry: ClassVar[dict[str, type]] = {}

    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        # Register the class only if not the base class and has a provider_name
        provider_name = attrs.get("provider_name")
        if bases and provider_name:
            cls.registry[provider_name] = cls
        return cls


class BaseProvider(metaclass=ProviderMeta):
    """Base class for all providers."""
    provider_name : str = ""
    async def generate_text(self, request: LLMRequest) -> str:
        """Common interface for all providers; gives back a coroutine, who use it must use await"""
        raise NotImplementedError("Subclasses must implement generate_text")
    

class FastProvider(BaseProvider):
    """provider fast and reliable"""
    provider_name = "fast"

    async def generate_text(self, request: LLMRequest) -> str:
        """small latency"""
        await asyncio.sleep(random.uniform(0.01, 0.03))
        return f"[fast:{request.tasktype.value}] Processed doc {request.doc_id}"    


class SlowProvider(BaseProvider):
    """provider slow and reliable"""
    provider_name = "slow"

    async def generate_text(self, request: LLMRequest) -> str:
        """large latency, every 20% of calls raises a ProviderTimeoutError"""
        latency = random.uniform(0.05, 0.2)
        await asyncio.sleep(latency)
        if random.random() < 0.2:
            # transsient, it will be retried from the orchestrator
            raise ProviderTimeoutError(
                f"Timeout for doc {request.doc_id}",
                timeout=latency,
            )        
        return f"[slow:{request.tasktype.value}] Processed doc {request.doc_id}"   


class RateLimitedProvider(BaseProvider):
    """Rate limited"""
    provider_name = "ratelimit"
    # call_count here to avoid reinitialization on each call, shared by all instances
    call_count: int = 0
    def __init__(self, max_calls_before_limit: int = 2) -> None:
        self.max_calls_before_limit = max_calls_before_limit    

    async def generate_text(self, request: LLMRequest) -> str:
        """every 3 calls raises a RateLimitError"""
        RateLimitedProvider.call_count += 1
        await asyncio.sleep(random.uniform(0.01, 0.03)) 
        if RateLimitedProvider.call_count % (self.max_calls_before_limit + 1) == 0:
            # every 3d call rate limit 429, next retry passes
            raise RateLimitError(f"Rate limit exceeded for doc {request.doc_id}", retry_after=1)
        return f"[ratelimit:{request.tasktype.value}] Processed doc {request.doc_id}"