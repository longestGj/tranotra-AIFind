.PHONY: help install run test lint format clean debug

help:
	@echo "Tranotra Leads - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install       Install dependencies via Poetry"
	@echo "  run           Run Flask development server"
	@echo "  test          Run pytest with coverage"
	@echo "  lint          Run code quality checks (black, isort, mypy)"
	@echo "  format        Format code with black and isort"
	@echo "  clean         Remove build artifacts and cache"
	@echo "  debug         Run Flask with debugger"

install:
	@echo "Installing dependencies with Poetry..."
	poetry install

run:
	@echo "Starting Flask development server..."
	poetry run flask run

test:
	@echo "Running tests with coverage..."
	poetry run pytest

lint:
	@echo "Running code quality checks..."
	poetry run black --check src/ tests/
	poetry run isort --check-only src/ tests/
	poetry run mypy src/

format:
	@echo "Formatting code with black and isort..."
	poetry run black src/ tests/
	poetry run isort src/ tests/
	@echo "Code formatted successfully"

clean:
	@echo "Cleaning up build artifacts..."
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/
	@echo "Cleanup complete"

debug:
	@echo "Starting Flask with debugger..."
	FLASK_ENV=development FLASK_DEBUG=True poetry run flask run
