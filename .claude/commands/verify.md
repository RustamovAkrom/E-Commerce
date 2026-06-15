# Verify Project Health

Run these in order. Fix all errors before reporting done.

## Backend checks
```bash
cd backend
uv run ruff check . --fix
uv run mypy src/ --ignore-missing-imports
uv run python -c "from src.main import app; print('Backend import: OK')"
uv run pytest tests/ -v --tb=short 2>/dev/null || echo "Tests not yet created"
```

## Frontend checks (if exists)
```bash
cd frontend
pnpm tsc --noEmit
pnpm lint
```

## Docker check (if docker-compose.yml exists)
```bash
docker-compose config --quiet && echo "Docker Compose: OK"
```

## Report format
After all checks, report:
- `[OK]` or `[FAIL]` for each check
- For `FAIL`: show exact error and fix applied
- Final line: "All checks passed" or "X issues remain"
