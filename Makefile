.PHONY: test-db-up test-db-down test-db-logs test test-integration

# Detect OS and set pytest command accordingly
ifeq ($(OS),Windows_NT)
    PYTEST = backend/.venv/Scripts/pytest.exe
    DOCKER_COMPOSE = docker compose
else
    PYTEST = pytest
    DOCKER_COMPOSE = docker compose
endif

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

# Run integration tests (starts DB if needed)
test-integration: test-db-up
	$(PYTEST) backend/tests/integration -v --tb=short
	$(MAKE) test-db-down

# Run all tests
test: test-db-up
	$(PYTEST) backend/tests -v --tb=short
	$(MAKE) test-db-down