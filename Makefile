# Makefile for AI Product Selector

.PHONY: help test compile-excel clean

help:
	@echo "Available commands:"
	@echo "  make test          - Run all tests"
	@echo "  make compile-excel - Compile Excel rules"
	@echo "  make clean        - Clean generated files"

# Compile Excel calculator to Python rules
compile-excel:
	@echo "Compiling Excel calculator..."
	python scripts/compile_excel.py docs/profits_calculator.xlsx -o common/excel_engine/
	@echo "Compilation complete"

# Run tests
test:
	python -m pytest tests/

test-unit:
	python -m pytest tests/unit/

test-integration:
	python -m pytest tests/integration/

# Clean generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*_compiled.json" -delete
	find . -type f -name "*_rules.py" -path "*/compiled/*" -delete

# Development setup
dev-setup:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt