# poetry add pytest only for dev #
poetry add --group dev pytest

# code verify #
ruff check . --fix

# tests #
poetry run pytest tests/test_models.py -v 

poetry run python -m unittest tests.test_retry -v
GREEN for 3 tests afrer correcting decorators.py

poetry run python -m unittest 


