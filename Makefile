.PHONY: dev prod stop logs migrate migration test lint snapshot session

# Development
dev:
	docker-compose -f docker-compose.dev.yml up

prod:
	docker-compose up -d

stop:
	docker-compose down

# Logs
logs:
	docker-compose logs -f backend

bot-logs:
	docker-compose logs -f bot

# Database
migrate:
	cd backend && uv run alembic upgrade head

migration:
	cd backend && uv run alembic revision --autogenerate -m "$(name)"

rollback:
	cd backend && uv run alembic downgrade -1

# Quality
test:
	cd backend && uv run pytest -v --tb=short

lint:
	cd backend && uv run ruff check . --fix && uv run mypy src/ --ignore-missing-imports

verify:
	cd backend && uv run python -c "from src.main import app; print('Backend: OK')"
	cd frontend && pnpm tsc --noEmit && echo "Frontend: OK"

# Claude Code helpers
snapshot:
	bash scripts/update_claude_snapshot.sh

session:
	bash scripts/new_session.sh

# Setup
install:
	cd backend && uv sync
	cd bot && uv sync
	cd frontend && pnpm install

# Docker
build:
	docker-compose build --no-cache

shell-backend:
	docker-compose exec backend uv run python

shell-db:
	docker-compose exec postgres psql -U postgres ecommerce
