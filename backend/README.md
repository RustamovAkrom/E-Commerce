# ECommerce Platform — Backend

FastAPI + SQLAlchemy (async) backend for the universal e-commerce platform.

See the repository root `README.md` for full documentation, architecture and
quickstart instructions.

## Local development

```bash
uv sync --extra dev          # install dependencies
uv run alembic upgrade head  # apply migrations
uv run uvicorn src.main:app --reload
```

## Quality

```bash
uv run ruff check .
uv run mypy src/
uv run pytest
```
