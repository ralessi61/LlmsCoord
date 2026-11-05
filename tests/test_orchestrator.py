import asyncio
import unittest
from unittest.mock import patch

from llmsharing.models import LLMRequest, OrchestratorConfig, TaskType
from llmsharing.orchestrator import AsyncioStrategy, ThreadingStrategy
from llmsharing.providers import FastProvider


class TestOrchestrator(unittest.IsolatedAsyncioTestCase):
    """Exercise the orchestrator strategies against realistic request batches."""

    def setUp(self):
        """Build a small shared configuration for each test case."""
        self.config = OrchestratorConfig(
            max_concurrency=2,
            max_tokens=100,
            temperature=0.2,
        )
        self.orch = AsyncioStrategy(self.config)


    async def fake_generate(self, request):
        """Simulate a fast provider with a slightly different delay per document."""
        if request.doc_id == "DOC-SLOW":
            await asyncio.sleep(0.05)
        else:
            await asyncio.sleep(0.005)
        return f"Result for {request.doc_id}"


    async def test_happy(self):
        """The happy path should process both requests successfully."""
        requests = [
            LLMRequest(doc_id="DOC-1", tasktype=TaskType.SUMMARY, prompt="First valid prompt"),
            LLMRequest(doc_id="DOC-2", tasktype=TaskType.SUMMARY, prompt="Second valid prompt"),
        ]
        batch = await self.orch.run(requests)
        self.assertEqual(batch.successful_requests, 2)
        self.assertEqual(batch.failed_requests, 0)
        self.assertEqual(batch.results[0].llmrequest_id, requests[0].request_id)
        self.assertEqual(batch.results[1].llmrequest_id, requests[1].request_id)


    async def test_out_of_order(self):
        """Results should keep the original request order even when completion times vary."""
        async def fake_generate(self_provider, request):
            if request.doc_id == "DOC-SLOW":
                await asyncio.sleep(0.05)
            else:
                await asyncio.sleep(0.005)
            return f"Result for {request.doc_id}"
        requests = [
            LLMRequest(doc_id="DOC-SLOW", tasktype=TaskType.SUMMARY, prompt="First request slow"),
            LLMRequest(doc_id="DOC-FAST", tasktype=TaskType.SUMMARY, prompt="Second request fast"),
        ]
        with patch.object(FastProvider, "generate_text", new=fake_generate):
            batch = await self.orch.run(requests)
        self.assertEqual(batch.results[0].llmrequest_id, requests[0].request_id)
        self.assertEqual(batch.results[0].output, "Result for DOC-SLOW")
        self.assertEqual(batch.results[1].llmrequest_id, requests[1].request_id)
        self.assertEqual(batch.results[1].output, "Result for DOC-FAST")


    async def test_max_concurrency(self):
        """The scheduler should never exceed the configured concurrency cap."""
        current = 0
        peak = 0

        async def tracked_generate(self_provider, request):
            nonlocal current, peak
            current += 1
            peak = max(peak, current)
            await asyncio.sleep(0.02)
            current -= 1
            return "ok"

        requests = [
            LLMRequest(doc_id=f"DOC-{i}", tasktype=TaskType.SUMMARY, prompt="Test concurrency limit")
            for i in range(6)
        ]
        with patch.object(FastProvider, "generate_text", new=tracked_generate):
            batch = await self.orch.run(requests)
        self.assertEqual(batch.successful_requests, 6)
        self.assertLessEqual(peak, 2)


    def test_threading_happy(self):
        """The threading strategy should handle a simple successful batch too."""
        orch = ThreadingStrategy(self.config)
        requests = [
            LLMRequest(doc_id="DOC-1", tasktype=TaskType.SUMMARY, prompt="First valid prompt"),
            LLMRequest(doc_id="DOC-2", tasktype=TaskType.SUMMARY, prompt="Second valid prompt"),
        ]
        batch = orch.run(requests)
        self.assertEqual(batch.successful_requests, 2)
        self.assertEqual(batch.failed_requests, 0)
