.PHONY: help install clean test figures verify all

help:
	@echo "available targets:"
	@echo "  install    - install dependencies"
	@echo "  clean      - remove generated files"
	@echo "  test       - run tests"
	@echo "  figures    - generate manuscript figures"
	@echo "  verify     - verify data integrity"
	@echo "  all        - run full analysis pipeline"

install:
	pip install -r requirements.txt

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache

test:
	pytest tests/ -v

figures:
	python scripts/generate_figures.py

verify:
	python scripts/normalized_concordance_analysis.py

all:
	@echo "running full analysis pipeline..."
	python scripts/phase1_document_inventory.py
	python scripts/phase1b_extract_documents.py
	python scripts/phase2_document_analysis.py
	python scripts/thematic_analysis.py
	python scripts/generate_manuscript_data.py
	python scripts/normalized_concordance_analysis.py
	python scripts/generate_figures.py
	@echo "analysis complete"
