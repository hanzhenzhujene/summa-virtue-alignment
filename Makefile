PYTHON ?= python3.12
VENV ?= .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
CLI := $(BIN)/summa-moral-graph
PYTEST := $(BIN)/pytest
RUFF := $(BIN)/ruff
MYPY := $(BIN)/mypy

.PHONY: install build-interim validate test lint typecheck check

$(BIN)/python:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

install: $(BIN)/python
	$(PIP) install -e ".[dev]"

build-interim: install
	$(CLI) build-interim

validate: install
	$(CLI) validate-interim

test: install
	$(PYTEST)

lint: install
	$(RUFF) check .

typecheck: install
	$(MYPY) src tests

check: lint typecheck test validate

