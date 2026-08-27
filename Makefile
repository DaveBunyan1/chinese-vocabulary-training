.PHONY: test-db-up test-db-down test-db-logs test test-unit test-integration test-file migrate seed-categories db-up db-down

# OS-Agnostic Executable Detection
ifeq ($(OS),Windows_NT)
    PYTHON := backend/.venv/Scripts/python.exe
    PYTEST := backend/.venv/Scripts/pytest.exe
    ALEMBIC := backend/.venv/Scripts/alembic.exe
else
    PYTHON := $(shell which python3 2>/dev/null || echo backend/.venv/bin/python)
    PYTEST := $(shell which pytest 2>/dev/null || echo backend/.venv/bin/pytest)
    ALEMBIC := $(shell which alembic 2>/dev/null || echo backend/.venv/bin/alembic)
endif

DOCKER_COMPOSE := docker compose

migrate:
	$(ALEMBIC) -c backend/alembic.ini upgrade head

# Spin up the primary local development database (docker-compose.yml)
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

# --- Seeding ---

# Ensure dev database is running, then execute seeding script inside virtualenv
# PYTHONPATH is set so the installed package (or src layout) is importable
seed-categories: db-up
	cd backend && PYTHONPATH=src $(PYTHON) -m chinese_learning.infrastructure.persistence.seed.seed_categories

# --- Testing ---
# Start the test Postgres container
test-db-up:
	$(DOCKER_COMPOSE) -f docker-compose.test.yml up -d
	@echo "Waiting for Postgres to become healthy..."
	@until $(DOCKER_COMPOSE) -f docker-compose.test.yml exec -T postgres-test pg_isready -U chinese -d chinese_learning_test > /dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "Postgres is ready on localhost:5433"

# Stop & remove the container + volume
test-db-down:
	$(DOCKER_COMPOSE) -f docker-compose.test.yml down -v

# Show logs
test-db-logs:
	$(DOCKER_COMPOSE) -f docker-compose.test.yml logs -f postgres-test

# Run unit tests (starts DB if needed)
test-unit: test-db-up
	$(PYTEST) backend/tests/unit -v --tb=short
	$(MAKE) test-db-down

# Run integration tests (starts DB if needed)
test-integration: test-db-up
	$(PYTEST) backend/tests/integration -v --tb=short
	$(MAKE) test-db-down

# Run a single test file (Usage: make test-file FILE=backend/tests/unit/test_cedict.py)
test-file: test-db-up
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify a file. Example: make test-file FILE=backend/tests/unit/test_cedict.py"; \
		exit 1; \
	fi
	$(PYTEST) $(FILE) -v --tb=short
	$(MAKE) test-db-down
	
# Run all tests
test: test-db-up
	$(PYTEST) backend/tests -v --tb=short
	$(MAKE) test-db-down

restart-dev: 
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up -d --build