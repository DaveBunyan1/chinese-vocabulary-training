# Chinese Vocabulary Training

A domain-driven platform designed to help Chinese learners build, organize, and track their vocabulary and character knowledge through real text analysis and structured exposure metrics.

## Architecture & Design

This project applies Domain-Driven Design (DDD) and Hexagonal Architecture.
The architectural decisions here were directly informed by lessons learned from a previous real-time audio processing app.

[Read the Engineering Retrospective: Lessons from the Violin App](docs/reflections/0001_violin_app_lessons.md)

---

## Current Phase: Phase 4 – First Vertical Slice ("Build My Knowledge")

**Goal:** Allow users to paste arbitrary Chinese text to automatically extract vocabulary/characters, calculate frequency metrics, update exposure profiles, and assign categories.

```text
[ Input Text ] ──> [ Text Analyzer ] ──> [ Exposure Engine ] ──> [ Category Assignee ] ──> [ User Profile ]
```

### Feature Roadmap (`feat/` branches)

| Branch / Feature                               | Status        | Description                                                                          |
| :--------------------------------------------- | :------------ | :----------------------------------------------------------------------------------- |
| `feat/analyse-text-usecase`                    | _Complete   _ | Tokenize text into words/characters using Jieba/HanLP pipeline with noise filtering. |
| `feat/import-vocabulary-from-text`             | _In Progress_ | Persist new words and character entities into the domain layer.                      |
| `feat/update-knowledge-on-exposure`            | _Pending_     | Trigger `with_exposure` Domain Events to update user knowledge profiles.             |
| `feat/assign-categories-to-vocabulary`         | _Pending_     | Tag imported vocabulary with thematic categories.                                    |
| `feat/rest-api-text-import`                    | _Pending_     | Fast API endpoints to handle text payload ingestion.                                 |
| `feat/frontend-text-import-and-knowledge-view` | _Pending_     | UI components for pasting text and visualizing exposure updates.                     |

---

## Stack & Dependencies

- **Language:** Python 3.10+
- **NLP & Segmentation:** `jieba` (Primary lightweight tokenizer), `types-jieba` (Type stubs)
- **Architecture:** Hexagonal / DDD

---

## Getting Started

### Local Setup (Without Docker)

### Prerequisites

- Python 3.10+
- `pip` and `venv` (standard Python library tools)

### Installation Steps

1. **Create and activate a virtual environment:**

   ```bash
   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows (CMD / PowerShell)
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **Install application with development dependencies:**

   ```bash
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

3. **Run Code Quality Checks & Tests:**

   ```bash
   # Run Linter & Formatter (Ruff)
   ruff check .
   ruff format . --check

   # Run Type Checks (Mypy)
   mypy src

   # Run Test Suite (Pytest)
   pytest
   ```

4. **Start the API server:**
   ```bash
   uvicorn chinese_learning.main:app --reload --port 8000
   ```

### Makefile Commands

A cross-platform Makefile is provided in the project root to manage database lifecycles, migrations, database seeding, and testing suites.

| Command               | Action                                                                                       |
| :-------------------- | :------------------------------------------------------------------------------------------- |
| make db-up            | "Starts Postgres via Docker, waits for health check, and runs Alembic migrations."           |
| make db-down          | Stops the dev database and wipes persistent volumes.                                         |
| make seed-categories  | Ensures DB is healthy and populates default categories via virtualenv script.                |
| make test             | "Spins up isolated test DB (localhost:5433), runs all tests, and tears down test container." |
| make test-unit        | Runs unit test suite (tests/unit).                                                           |
| make test-integration | Runs integration test suite (tests/integration).                                             |

### Docker Setup

### 1. Full Stack (Backend + Database)

To spin up both the FastAPI backend (with live code reload on ./backend/src) and the PostgreSQL database:

```bash
docker compose up --build
```

The API will be accessible at http://localhost:8000.
