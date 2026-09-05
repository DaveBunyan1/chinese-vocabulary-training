.PHONY: help test-db-up test-db-down test-db-logs test test-unit test-integration test-file migrate seed-categories db-up db-down restart-dev

# ---------------------------------------------------------------------------
# Tool detection – always prefer the project virtualenv when present
# ---------------------------------------------------------------------------
ifeq ($(OS),Windows_NT)
    VENV_PYTHON := backend/scripts/python.exe
    # Fallback check for standard Windows venv structure using forward slashes:
    VENV_PYTHON := backend/.venv/Scripts/python.exe
    VENV_PYTEST := backend/.venv/Scripts/pytest.exe
    VENV_ALEMBIC := backend/.venv/Scripts/alembic.exe
    VENV_RUFF := backend/.venv/Scripts/ruff.exe
    VENV_MYPY := backend/.venv/Scripts/mypy.exe
else
    VENV_PYTHON := backend/.venv/bin/python
    VENV_PYTEST := backend/.venv/bin/pytest
    VENV_ALEMBIC := backend/.venv/bin/alembic
    VENV_RUFF := backend/.venv/bin/ruff
    VENV_MYPY := backend/.venv/bin/mypy
endif

# Prefer venv binaries if they exist, otherwise fall back to PATH
PYTHON  := $(shell test -x "$(VENV_PYTHON)"  && echo "$(VENV_PYTHON)"  || command -v python3 2>/dev/null || echo python3)
PYTEST  := $(shell test -x "$(VENV_PYTEST)"  && echo "$(VENV_PYTEST)"  || command -v pytest  2>/dev/null || echo pytest)
ALEMBIC := $(shell test -x "$(VENV_ALEMBIC)" && echo "$(VENV_ALEMBIC)" || command -v alembic 2>/dev/null || echo alembic)
RUFF    := $(shell test -x "$(VENV_RUFF)"    && echo "$(VENV_RUFF)"    || command -v ruff    2>/dev/null || echo ruff)
MYPY    := $(shell test -x "$(VENV_MYPY)"    && echo "$(VENV_MYPY)"    || command -v mypy    2>/dev/null || echo mypy)

DOCKER_COMPOSE := docker compose

help:
	@echo "Available targets:"
	@echo "  db-up              Start Postgres + run migrations"
	@echo "  db-down            Stop containers and remove volumes"
	@echo "  seed-categories    Seed default categories"
	@echo "  test               Full test suite (ephemeral test DB)"
	@echo "  test-unit          Unit tests only (no Docker)"
	@echo "  test-integration   Integration tests only"
	@echo "  test-file FILE=... Run a single test file"
	@echo "  lint               Ruff check + format check + Mypy"
	@echo "  format             Ruff format (in-place)"
	@echo "  restart-dev        Rebuild and restart full Docker stack"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
migrate:
	$(ALEMBIC) -c backend/alembic.ini upgrade head

db-up:
	$(DOCKER_COMPOSE) up -d --remove-orphans db
	@echo "Waiting for development Postgres to become healthy..."
	@until $(DOCKER_COMPOSE) exec -T db pg_isready -U chinese -d chinese_learning > /dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "Development Postgres is ready. Running migrations..."
	$(MAKE) migrate
	@echo "Migrations complete"

db-down:
	$(DOCKER_COMPOSE) down -v

# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------
seed-categories: db-up
	PYTHONPATH=$(REPO_ROOT)/backend/src $(PYTHON) -m chinese_learning.infrastructure.persistence.seed.seed_categories

seed-hsk: db-up seed-categories
	PYTHONPATH=$(REPO_ROOT)/backend/src $(PYTHON) -m chinese_learning.infrastructure.persistence.seed.seed_hsk_vocabulary

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------
test-db-up:
	$(DOCKER_COMPOSE) -f docker-compose.test.yml up -d
	@echo "Waiting for Postgres to become healthy..."
	@until $(DOCKER_COMPOSE) -f docker-compose.test.yml exec -T postgres-test pg_isready -U chinese -d chinese_learning_test > /dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "Postgres is ready on localhost:5433"

test-db-down:
	$(DOCKER_COMPOSE) -f docker-compose.test.yml down -v

test-db-logs:
	$(DOCKER_COMPOSE) -f docker-compose.test.yml logs -f postgres-test

# Unit tests are pure (mocks only) – no Postgres required
test-unit:
	$(PYTEST) backend/tests/unit -v --tb=short -m "not integration"

test-integration: test-db-up
	$(PYTEST) backend/tests/integration -v --tb=short
	$(MAKE) test-db-down

# Usage: make test-file FILE=backend/tests/unit/test_cedict.py
test-file: test-db-up
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify a file. Example: make test-file FILE=backend/tests/unit/test_cedict.py"; \
		exit 1; \
	fi
	$(PYTEST) $(FILE) -v --tb=short
	$(MAKE) test-db-down

test: test-db-up
	$(PYTEST) backend/tests -v --tb=short
	$(MAKE) test-db-down

# ---------------------------------------------------------------------------
# Lint / format
# ---------------------------------------------------------------------------
lint:
	cd backend && $(RUFF) check .
	cd backend && $(RUFF) format --check .
	cd backend && $(MYPY) src

format:
	cd backend && $(RUFF) check . --fix
	cd backend && $(RUFF) format .

# ---------------------------------------------------------------------------
# Docker helpers
# ---------------------------------------------------------------------------
restart-dev:
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up -d --build

restart-fresh:
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) up -d --build