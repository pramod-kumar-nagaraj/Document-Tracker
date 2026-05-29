.PHONY: lint format test check all clean

# Run ruff linter
lint:
	@echo Running ruff check...
	@ruff check src/ tests/

# Auto-fix lint issues
lint-fix:
	@echo Running ruff check --fix...
	@ruff check --fix src/ tests/

# Check formatting
format-check:
	@echo Running ruff format check...
	@ruff format --check --diff src/ tests/

# Auto-format code
format:
	@echo Formatting code...
	@ruff format src/ tests/

# Run tests
test:
	@echo Running tests...
	@pytest tests/ -v

# Run tests with coverage
test-cov:
	@echo Running tests with coverage...
	@pytest tests/ -v --cov=src --cov-report=term-missing

# Run all checks (CI)
check: lint format-check test
	@echo All checks passed!

# Install dev dependencies
install-dev:
	pip install -r dev-requirements.txt

# Clean generated files
clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
