.PHONY: test-db-up test-db-down test-db-logs test-integration test

# Start the test Postgres container and wait until healthy
test-db-up:
	docker compose -f docker-compose.test.yml up -d --remove-orphans
	@echo "Waiting for Postgres to become healthy..."
	@until docker compose -f docker-compose.test.yml exec -T postgres-test pg_isready -U chinese -d chinese_learning_test > /dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "Postgres is ready on localhost:5433"

# Stop & remove the container + volume
test-db-down:
	docker compose -f docker-compose.test.yml down -v

# Show logs
test-db-logs:
	docker compose -f docker-compose.test.yml logs -f postgres-test

# Run only integration tests using Poetry/Python venv runner
test-integration: test-db-up
	backend/.venv/Scripts/pytest.exe backend/tests/integration/ -v --tb=short 

	$(MAKE) test-db-down

# Run all tests (unit + integration)
test: test-db-up
	backend/.venv/Scripts/pytest.exe backend/tests/ -v --tb=short 
	$(MAKE) test-db-down