.PHONY: install clean run run-network help test venv-install format check

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies using pipenv"
	@echo "  make clean      - Remove virtual environment and cached files"
	@echo "  make run        - Run the Streamlit app locally (http://localhost:8501)"
	@echo "  make run-network- Run the Streamlit app accessible from network (http://0.0.0.0:8501)"
	@echo "  make test       - Run the test suite"
	@echo "  make venv-install - Install in a Python virtual environment"
	@echo "  make format     - Format code using Black"
	@echo "  make check      - Check if code formatting is correct"

check-python:
	@python3 -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11 or higher is required"'

install: check-python
	brew install pipx || true
	pipx ensurepath
	pipx install pipenv
	pipenv install --dev

clean:
	pipenv --rm || true
	rm -rf venv/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run: check-python install
	pipenv run pip install -e .
	pipenv run streamlit run src/datacompy_web_ui/ui/app.py

run-network: check-python install
	pipenv run pip install -e .
	pipenv run streamlit run src/datacompy_web_ui/ui/app.py --server.address 0.0.0.0

venv-install: check-python
	python3 -m venv venv
	. venv/bin/activate && pip install -e .

test: check-python install
	pipenv run pip install -e .
	pipenv run pytest tests/ -v

format: check-python install
	pipenv run black src/ tests/

check: check-python install
	pipenv run black --check src/ tests/

# Default target
.DEFAULT_GOAL := help 