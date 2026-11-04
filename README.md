poetry add --group dev pytest
ruff check . --fix

poetry run pytest tests/test_models.py -v 
in current push
==================================================================================== short test summary info =====================================================================================
FAILED tests/test_models.py::test_request_accepts_and_strips_prompt - pydantic_core._pydantic_core.ValidationError: 1 validation error for LLMRequest
FAILED tests/test_models.py::test_request_requires_prompt - Failed: DID NOT RAISE ValueError

A valid prompt is rejected: the condition in the validator is inverted.
A missing prompt is accepted: the field is optional (Optional[str] = None).