import pytest

from llmsharing.models import LLMRequest, TaskType


def test_request_accepts_and_strips_prompt():
    request = LLMRequest(
        doc_id="doc-1",
        tasktype=TaskType.SUMMARY,
        prompt="  Riassumi il documento  ",
    )

    assert request.prompt == "Riassumi il documento"


def test_request_requires_prompt():
    with pytest.raises(ValueError):
        LLMRequest(
            doc_id="doc-1",
            tasktype=TaskType.SUMMARY,
        )


def test_request_rejects_prompt_shorter_than_three_characters():
    with pytest.raises(ValueError):
        LLMRequest(
            doc_id="doc-1",
            tasktype=TaskType.SUMMARY,
            prompt=" a ",
        )