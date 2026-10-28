package={{ package_name }}

.PHONY: clean build clean-build clean-pyc clean-test docs docs-serve format lint check lint-check install sync test coverage

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

build: clean
	uv build

clean-build: ## remove build artifacts
	rm -fr out/
	rm -fr build/
	rm -fr .build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr .tox .ruff_cache .mypy_cache
	rm -fr cov.xml
	rm -fr coverage.xml
	rm -fr dump.rdb
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache
	rm -fr tests/.pytest_cache

docs: ## build the MkDocs documentation site
{% if use_mkdocs %}	uv run mkdocs build
{% else %}	@echo "MkDocs support is disabled; enable it when generating the scaffold."
{% endif %}

docs-serve: ## preview documentation with live reload
{% if use_mkdocs %}	uv run mkdocs serve
{% else %}	@echo "MkDocs support is disabled; enable it when generating the scaffold."
{% endif %}

format: ## apply safe Ruff fixes and format Python files
{% if use_ruff %}	uv run ruff check --fix .
	uv run ruff format .
{% endif %}{% if use_black %}	uv run black .
{% endif %}{% if use_isort %}	uv run isort --profile black .
{% endif %}{% if not (use_ruff or use_black or use_isort) %}	@echo "No formatters are enabled in this scaffold."
{% endif %}

lint:
{% if use_ruff %}	uv run ruff check .
{% endif %}{% if use_black %}	uv run black --check .
{% endif %}{% if use_isort %}	uv run isort --check-only --profile black .
{% endif %}{% if use_pylint %}	uv run pylint --exit-zero src
{% endif %}{% if use_mypy %}	uv run mypy --ignore-missing-imports src
{% endif %}{% if not (use_ruff or use_black or use_isort or use_pylint or use_mypy) %}	@echo "No linters are enabled in this scaffold."
{% endif %}

check:
{% if use_mypy %}	uv run mypy src
{% else %}	@echo "mypy is disabled; enable it when generating the scaffold."
{% endif %}

lint-check: lint check

install: clean
	uv sync --no-dev

sync: ## install or update the project environment and dependencies
	uv sync

test: ## run tests quickly with the default Python
{% if use_pytest %}	uv run pytest ./tests
{% else %}	@echo "pytest is disabled; enable it when generating the scaffold."
{% endif %}

{% if use_coverage and use_pytest %}coverage: ## create an HTML coverage report
	uv run pytest ./tests
	@echo "Coverage HTML report is available at htmlcov/index.html"
{% else %}coverage: ## show coverage availability
	@echo "Coverage is disabled; enable coverage when generating the scaffold."
{% endif %}
