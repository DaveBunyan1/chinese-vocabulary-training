# Backend – Chinese Learning Platform

This directory contains the FastAPI backend, domain model, infrastructure adapters, and tests.

## Quick reference

- **Package name:** `chinese-learning`
- **Entrypoint:** `chinese_learning.app:app`
- **Python:** ≥ 3.14 (see `pyproject.toml`)
- **Primary docs:** See the [root README](../README.md)

## Local development

From the **repository root**:

```bash
# Create venv inside backend/ (recommended)
cd backend
python3.14 -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# Install in editable mode + dev tools
cd ..
pip install -e "./backend[dev]"

# Start DB + migrate
make db-up

# Run API
uvicorn chinese_learning.app:app --reload --port 8000
```

## Layout

```
src/chinese_learning/
├── domain/           # Pure domain (entities, aggregates, value objects)
├── application/      # Use cases & application services
├── infrastructure/   # DB, NLP, telemetry, seed scripts
└── presentation/     # FastAPI routers & Pydantic schemas
tests/
migrations/
```

For architecture details see `docs/architecture.md` and `docs/domain_model.md` in the repository root.
