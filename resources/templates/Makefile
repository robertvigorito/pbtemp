.PHONY: install test lint format clean

install:
	uv sync

{% if use_pytest %}test:
	uv run pytest

{% endif %}{% if use_ruff %}lint:
	uv run ruff check .

format:
	uv run ruff format .

{% endif %}clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov dist build
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete
