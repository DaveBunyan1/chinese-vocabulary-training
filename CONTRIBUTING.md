# Contributing

Thanks for your interest in improving the Chinese Vocabulary Training platform.

## Development setup

Follow the **Quick Start** or **Local Development** sections in the [README](README.md).

In short:

```bash
# Full stack (recommended)
docker compose up --build

# Backend-only local development
cd backend && python3.14 -m venv .venv && source .venv/bin/activate
cd .. && pip install -e "./backend[dev]"
make db-up
uvicorn chinese_learning.app:app --reload --port 8000
```

## Code quality

Before opening a PR:

1. **Format & lint** (Ruff)

    ```bash
    cd backend
    ruff check . --fix
    ruff format .
    ```

2. **Type check** (Mypy, strict)

    ```bash
    cd backend
    mypy src
    ```

3. **Tests**
    ```bash
    make test          # full suite
    # or
    make test-unit
    make test-integration
    ```

Pre-commit hooks are configured (`.pre-commit-config.yml`). Install them with:

```bash
pip install pre-commit
pre-commit install
```

## Project conventions

- **Architecture**: Domain-Driven Design + Hexagonal Architecture. Keep the domain layer pure (no FastAPI, SQLAlchemy, or HTTP imports).
- **Python**: 3.14+ (pinned via `.python-version`), type hints required, strict Mypy.
  Prefer the project venv at `backend/.venv`. Full tests run in CI / via `make test`; pre-commit only runs fast checks (Ruff + Mypy).
- **Commits**: Prefer conventional-style messages (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).
- **Branches**: Feature work on `feat/...` or `fix/...` branches; open PRs against `main`.

## Documentation

- Domain and architecture decisions live in `docs/`.
- Keep the root `README.md` accurate when setup or status changes.
- Update `TODO.md` when closing items or adding new known issues.

## Questions / scope

This is currently an MVP-focused project. Prefer stabilising existing vertical slices (dashboards, practice, data quality) before large new features. See `TODO.md` for the current prioritised list.
