.PHONY: test test-unit test-integration test-coverage test-fast clean help

help:
	@echo "Document Intelligence Refinery - Test Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make test              Run all tests (unit + integration)"
	@echo "  make test-unit         Run unit tests only"
	@echo "  make test-integration  Run integration tests only"
	@echo "  make test-coverage     Run tests with coverage report"
	@echo "  make test-fast         Run tests without coverage (faster)"
	@echo "  make test-watch        Run tests in watch mode"
	@echo "  make clean             Clean test artifacts"
	@echo ""

test:
	@echo "Running all tests..."
	@python3 run_tests.py

test-unit:
	@echo "Running unit tests..."
	@pytest tests/unit/ -v --tb=short

test-integration:
	@echo "Running integration tests..."
	@pytest tests/integration/ -v --tb=short

test-coverage:
	@echo "Running tests with coverage..."
	@pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "Coverage report: htmlcov/index.html"

test-fast:
	@echo "Running tests (fast mode)..."
	@pytest tests/ -v --tb=short -x

test-watch:
	@echo "Running tests in watch mode..."
	@pytest-watch tests/ -- -v --tb=short

test-specific:
	@echo "Run specific test: make test-specific TEST=tests/unit/test_triage.py"
	@pytest $(TEST) -v

clean:
	@echo "Cleaning test artifacts..."
	@rm -rf .pytest_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@rm -rf **/__pycache__
	@rm -rf **/*.pyc
	@echo "Clean complete!"
