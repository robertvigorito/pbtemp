
package={{ pktemp.package_name }}

.PHONY: docs docs-serve format

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

build: clean
	$(eval BUILD_LOCATION=./.build)
	pip install . -t $(BUILD_LOCATION) --upgrade

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

clean: clean-test clean-build clean-pyc

docs: ## build the MkDocs documentation site
	uv run --python 3.12 mkdocs build

docs-serve: ## preview documentation with live reload
	uv run --python 3.12 mkdocs serve

format: ## apply safe Ruff fixes and format Python files
	uv run ruff check --fix src tests
	uv run ruff format src tests

lint: 
	$(eval files=$(shell find ./src -type f -name "*.py"))
	@ruff check $(files)
	@isort --check-only --color  $(files) --profile black || echo "isort failed" 
	@black --check $(files) || echo "black failed"
	@pylint --exit-zero $(files)

check:
	@mypy ./src

lint-check: lint check

install: clean
	pip install --upgrade .

poetry-install: clean
	poetry install 

test: ## run tests quickly with the default Python
	pytest --cov=$(package) --cov-report=term-missing --cov-fail-under=70 --cov-config=.coveragerc --cov-report=html ./tests
	pytest --cov=$(package) --cov-report=term-missing --cov-fail-under=70 --cov-config=.coveragerc --cov-report=html ./tests

test-all: ## run tests on every Python version with tox
	tox

script:
	$(eval SCRIPTS=$(shell find ./scripts -type f -name "*"))
	@install -v -m 555 $(SCRIPTS) /software/scripts/

coverage: ## check code coverage quickly with the default Python
	wslview ./htmlcov/index.html