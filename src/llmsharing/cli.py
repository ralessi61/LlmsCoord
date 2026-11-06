import asyncio
import logging

from llmsharing import logger
from llmsharing.models import LLMRequest, OrchestratorConfig, TaskType
from llmsharing.orchestrator import AsyncioStrategy


def main() -> None:
    logger.setup_logging()
    log = logging.getLogger(__name__)
    config = OrchestratorConfig(
            max_concurrency=2,
            max_tokens=100,
            temperature=0.2,
    )

    requests = [
        LLMRequest(
            doc_id="doc-1",
            tasktype=TaskType.SUMMARY,
            prompt="Summarize this document",
        ),
        LLMRequest(
            doc_id="doc-2",
            tasktype=TaskType.QUESTION_ANSWERING,
            prompt="What is the main point?",
        ),
        LLMRequest(
            doc_id="doc-3",
            tasktype=TaskType.EXTRACTION,
            prompt="Extract today news",
            fields=['Day', 'Nation']
        ),
        LLMRequest(
            doc_id="doc-4",
            tasktype=TaskType.CLASSIFICATION,
            prompt="What animal in this image",
        ),        
        LLMRequest(
            doc_id="doc-5",
            tasktype=TaskType.TRANSLATION,
            prompt="Translate dog in Italian",
        ),
        LLMRequest(
            doc_id="doc-6",
            tasktype=TaskType.DETECTION,
            prompt="Detect if this email is fraud attempt",
        )       
    ]
    
    batch = asyncio.run(AsyncioStrategy(config).run(requests))
    log.info(
        "done: %s ok, %s failed, retries=%s",
        batch.successful_requests,
        batch.failed_requests,
        batch.total_retries,
    )


if __name__ == "__main__": 
    main()