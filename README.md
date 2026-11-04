# poetry add pytest only for dev #
poetry add --group dev pytest

# code verify #
ruff check . --fix

# tests #
poetry run pytest tests/test_models.py -v 


