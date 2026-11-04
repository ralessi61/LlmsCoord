import asyncio
import time

from llmsharing.exceptions import CoordinatorError
from llmsharing.models import BatchResult, LLMRequest, OrchestratorConfig, TaskResult
from llmsharing.providers import BaseProvider


class AsyncioStrategy:
    def __init__(self, config: OrchestratorConfig, provider: BaseProvider) -> None:
        """Initialize the orchestrator with configuration and provider."""
        self._sem = asyncio.Semaphore(config.max_concurrency)
        self.provider = provider

    async def _handle(self, request: LLMRequest) -> TaskResult:
        """Handle a single LLMRequest, managing concurrency and error handling."""
        async with self._sem:
            start = time.perf_counter()
            try:
                output = await self.provider.generate_text(request)
            except CoordinatorError  as e:
                return TaskResult(
                    success=False,
                    error_message=str(e),
                    llmrequest_id=request.request_id,
                    tasktype=request.tasktype,
                    status="failed",
                    latency=time.perf_counter() - start,
                    retries=0,
                    tokens_estimated=0
                )
            return TaskResult(
                success=True,
                output=output,
                llmrequest_id=request.request_id,
                tasktype=request.tasktype,
                status="ok",
                latency=time.perf_counter() - start,
                retries=0,
                tokens_estimated=max(1, len(output) // 4)
            )


    async def run(self, requests: list[LLMRequest]) -> BatchResult:
        """Run a batch of LLMRequests concurrently, returning a BatchResult."""
        tasks = [self._handle(r) for r in requests]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        return self._report(requests, outcomes)
    

    def _report(self, requests: list[LLMRequest], results: list) -> BatchResult:
        """Generate a BatchResult from the outcomes of the requests."""
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