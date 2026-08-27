# Chinese Vocabulary Training

A domain-driven platform that helps Chinese learners build, organise, and track vocabulary and character knowledge through real-text analysis, structured exposure metrics, and adaptive practice.

## Architecture

This project applies **Domain-Driven Design (DDD)** and **Hexagonal (Ports & Adapters) Architecture**.

Business rules live in a pure domain layer. Infrastructure (database, NLP, HTTP) is isolated behind ports so the core remains testable and framework-agnostic.

Architectural decisions were informed by lessons from a previous real-time audio processing project:

→ [Engineering Retrospective: Lessons from the Violin App](docs/reflections/0001_violin_app_lessons.md)

Key design documents:

| Document                                 | Description                                        |
| ---------------------------------------- | -------------------------------------------------- |
| [Product Vision](docs/product_vision.md) | Goals, learning activities, MVP scope              |
| [Domain Model](docs/domain_model.md)     | Core entities, aggregates, and ubiquitous language |
| [Architecture](docs/architecture.md)     | Layers, ports, and component boundaries            |
| [Roadmap](docs/ROADMAP.md)               | Phased delivery plan                               |
| [Context Map](docs/context_map.md)       | Bounded contexts                                   |

## Current Status

The project is past the initial vertical slice and already includes:

- Text import & analysis (jieba + pypinyin)
- Vocabulary & character knowledge tracking
- Practice sessions (recall / recognition)
- Vocabulary & character dashboards with filtering
- Category management
- Basic progress metrics and review queue scaffolding

See `TODO.md` for known bugs and the next polish items.

## Stack

| Layer    | Technology                                                                         |
| -------- | ---------------------------------------------------------------------------------- |
| Backend  | Python **3.14+**, FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic v2              |
| NLP      | jieba, pypinyin                                                                    |
| Database | PostgreSQL 16                                                                      |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, TanStack Query                         |
| Tooling  | Ruff, Mypy (strict), Pytest, pre-commit, Docker Compose, structlog + OpenTelemetry |

> **Note:** The project targets **Python 3.14+** (stable since October 2025).  
> A `.python-version` file is provided for pyenv / asdf. Docker images and CI also use 3.14.

## Quick Start (Recommended: Docker Compose)

The easiest way to run the full stack:

```bash
# From the repository root
docker compose up --build
```

| Service            | URL                          |
| ------------------ | ---------------------------- |
| Backend API        | http://localhost:8000        |
| API docs (Swagger) | http://localhost:8000/docs   |
| Frontend           | http://localhost:3000        |
| Health check       | http://localhost:8000/health |

The backend mounts `./backend/src` for live reload. Postgres data is persisted in a Docker volume.

To stop and remove volumes:

```bash
docker compose down -v
```

## Local Development (Backend only)

### Prerequisites

- Python **3.14+**
- Docker (for the database)
- `pip` / `venv`

### 1. Create a virtual environment

```bash
cd backend
python3.14 -m venv .venv          # or python3 -m venv .venv if 3.14 is default

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 2. Install the package + dev dependencies

From the **repository root**:

```bash
pip install --upgrade pip
pip install -e "./backend[dev]"
```

### 3. Start the database & run migrations

```bash
# From repository root
make db-up
```

This starts Postgres, waits for it to become healthy, and applies Alembic migrations.

Optionally seed default categories (HSK levels + topics):

```bash
make seed-categories
```

### 4. Run the API

```bash
# From repository root (with venv active)
uvicorn chinese_learning.app:app --reload --port 8000
```

The application entrypoint is `chinese_learning.app:app` (see `backend/src/chinese_learning/app.py`).

### 5. Quality checks & tests

```bash
# From backend/ (or adjust paths)
cd backend
ruff check .
ruff format --check .
mypy src
```

Full test suite (spins up an isolated test database on port 5433):

```bash
# From repository root
make test
# or
make test-unit
make test-integration
```

## Makefile Targets

| Command                   | Description                                     |
| ------------------------- | ----------------------------------------------- |
| `make help`               | List available targets                          |
| `make db-up`              | Start Postgres, wait for health, run migrations |
| `make db-down`            | Stop containers and remove volumes              |
| `make seed-categories`    | Seed default categories (requires DB)           |
| `make test`               | Run full test suite against ephemeral test DB   |
| `make test-unit`          | Unit tests only                                 |
| `make test-integration`   | Integration tests only                          |
| `make test-file FILE=...` | Run a single test file                          |
| `make lint`               | Ruff check + format check + Mypy                |
| `make format`             | Auto-fix + format with Ruff                     |
| `make restart-dev`        | Rebuild and restart the full Docker stack       |

## Frontend Development

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (or configured port)
```

The production frontend is served via the Docker Compose `frontend` service on port 3000. The Vite dev server is useful for rapid UI work; point it at the backend running on `:8000`.

## Environment Variables

Copy the example file:

```bash
cp .env.example .env
```

| Variable       | Purpose                            | Default (dev)                                                          |
| -------------- | ---------------------------------- | ---------------------------------------------------------------------- |
| `ENVIRONMENT`  | Runtime environment                | `development`                                                          |
| `PORT`         | API port                           | `8000`                                                                 |
| `LOG_LEVEL`    | Logging level                      | `INFO`                                                                 |
| `DATABASE_URL` | Async SQLAlchemy connection string | `postgresql+asyncpg://chinese:chinese@localhost:5432/chinese_learning` |

When running inside Docker Compose the `DATABASE_URL` is overridden to use the `db` service hostname.

## Project Layout

```
.
├── backend/
│   ├── src/chinese_learning/
│   │   ├── domain/           # Pure domain model (entities, aggregates, value objects)
│   │   ├── application/      # Use cases & application services
│   │   ├── infrastructure/   # Adapters (DB, NLP, telemetry)
│   │   └── presentation/     # FastAPI routers & schemas
│   ├── tests/
│   ├── migrations/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                 # React + TypeScript + Vite + Tailwind
├── docs/                     # Architecture, domain model, ADRs, RFCs
├── docker-compose.yml
├── Makefile
└── TODO.md
```

## Contributing / Next Steps

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, quality checks, and conventions.

See `TODO.md` for the current prioritised list of bug fixes, polish items, and upcoming enhancements.

Before adding new features, the immediate focus is stabilising the existing vertical slices (dashboard filtering, definition quality, test coverage, and documentation accuracy).

This project is released under the [MIT License](LICENSE).
