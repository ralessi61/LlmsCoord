poetry add --group dev pytest
ruff check . --fix

poetry run pytest tests/test_models.py -v 
in current push green phase:

tests/test_models.py::test_request_accepts_and_strips_prompt PASSED                                                                                                                         [ 33%]
tests/test_models.py::test_request_requires_prompt PASSED                                                                                                                                   [ 66%]
tests/test_models.py::test_request_rejects_prompt_shorter_than_three_characters PASSED                                                                                                      [100%]

======================================================================================= 3 passed in 0.11s ========================================================================================