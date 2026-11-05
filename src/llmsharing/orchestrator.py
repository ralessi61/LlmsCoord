import asyncio
import time

from llmsharing.decorators import (
    call_counter,
    get_retry_count,
    measure_execution_time,
    retry,
)
from llmsharing.exceptions import CoordinatorError, ProviderNotFoundError
from llmsharing.models import BatchResult, LLMRequest, OrchestratorConfig, TaskResult
from llmsharing.providers import BaseProvider


class AsyncioStrategy:
    def __init__(self, config: OrchestratorConfig) -> None:
        """Initialize the orchestrator with configuration and provider."""
        self._sem = asyncio.Semaphore(config.max_concurrency)

    async def _handle(self, request: LLMRequest) -> TaskResult:
        """Handle a single LLMRequest, managing concurrency and error handling."""
        async with self._sem:
            start = time.perf_counter()
            try:
                output = await self._call_provider(request)

            except CoordinatorError  as e:
                return TaskResult(
                    success=False,
                    error_code=e.status_code,
                    error_message=str(e),
                    llmrequest_id=request.request_id,
                    tasktype=request.tasktype,
                    status="failed",
                    latency=time.perf_counter() - start,
                    retries=get_retry_count(),
                    tokens_estimated=0
                )
            return TaskResult(
                success=True,
                output=output,
                llmrequest_id=request.request_id,
                tasktype=request.tasktype,
                status="ok",
                latency=time.perf_counter() - start,
                retries=get_retry_count(),
                tokens_estimated=max(1, len(output) // 4)
            )


    async def run(self, requests: list[LLMRequest]) -> BatchResult:
        """Run a batch of LLMRequests concurrently, returns a BatchResult."""
        tasks = [self._handle(r) for r in requests]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        return self._report(requests, outcomes)
    

    def _report(self, requests: list[LLMRequest], results: list) -> BatchResult:
        """Generate a BatchResult from the outcomes of requests."""
        results = [o for o in results if isinstance(o, TaskResult)]
        return BatchResult(
            total_requests=len(requests),
            successful_requests=sum(r.success for r in results),
            failed_requests=len(requests) - sum(r.success for r in results),
            total_tokens_used=sum(r.tokens_estimated for r in results),
            total_latency=sum(r.latency for r in results),
            total_retries=sum(r.retries for r in results),
            results=results
        )


    @call_counter   
    @retry()   # () requested, is a factory
    @measure_execution_time  
    async def _call_provider(self, request: LLMRequest)-> str:
        """call to provider"""
        provider_cls = BaseProvider.registry.get(request.provider)
        if provider_cls is None:
            raise ProviderNotFoundError(
                f"Provider unknown: {request.provider}"
            )
        provider = provider_cls()
        return await provider.generate_text(request)