# CLAUDE.md — Project Brain

## CRITICAL RULES (read first, never violate)
- Package manager: `uv` ONLY. Never pip. Never poetry.
  Install: `uv add pkg` | Run: `uv run cmd` | Sync: `uv sync`
- No placeholders. No `# TODO`. No `pass` in service/repository methods.
- Every router endpoint: `response_model=` must be set.
- Every service/repository method: full type annotations required.
- No `Any` type without inline comment justifying it.
- No hardcoded secrets. All from `settings.*`
- No raw SQL with f-strings. SQLAlchemy ORM only.
- No direct DB access in bot/. Bot uses httpx -> backend API only.

## ARCHITECTURE (Single Responsibility — strict)
| File            | Responsibility                              | Forbidden             |
|-----------------|---------------------------------------------|-----------------------|
| router.py       | HTTP layer. Parse request. Call service.    | Business logic, DB    |
| service.py      | Business logic. Call repository.            | HTTP concepts, DB     |
| repository.py   | DB queries. Inherit BaseRepository.         | Business logic, HTTP  |
| schemas.py      | Pydantic I/O only. *Request/*Response/*DB   | Logic                 |
| models.py       | SQLAlchemy models only.                     | Methods with logic    |

## MODULE CREATION CHECKLIST (always in this order)
1. models.py   (UUID PK, TimestampMixin, SoftDeleteMixin, indexes on FKs)
2. schemas.py  (separate: *Request, *Response, *DB)
3. repository.py (inherit BaseRepository from core/base_repository.py)
4. service.py
5. router.py   (response_model on every endpoint)
6. Wire into main.py

## DATABASE MODEL STANDARDS
Every model MUST have:
- `id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)`
- `created_at`, `updated_at` via TimestampMixin
- `is_deleted: Mapped[bool]` via SoftDeleteMixin
- Index on every FK column
- Index on every column used in WHERE/ORDER BY

## SECURITY CHECKLIST (enforce on every endpoint)
- Auth endpoints: rate limited via slowapi
- Protected endpoints: `Depends(get_current_user)`
- Admin endpoints: `Depends(require_role(UserRole.ADMIN))`
- File uploads: validate MIME type + extension + max 10MB
- Payment webhooks: verify signature before processing
- CORS: from settings.ALLOWED_ORIGINS only, never hardcode "*"
- JWT: access=15min, refresh=30d, rotation on use, blacklist on logout

## MARKETPLACE TOGGLE
```python
# main.py pattern — conditional router registration
if settings.MARKETPLACE_MODE:
    app.include_router(vendors_router, prefix="/api/v1/vendors", tags=["vendors"])
```
MARKETPLACE_MODE=False: vendors module written but NOT wired
MARKETPLACE_MODE=True: vendors module active

## PAYMENT PROVIDERS
All providers inherit core/payments/base.py abstract class. Methods: create_payment(), verify_webhook(), refund()
Providers: Click (UZ), Payme (UZ), Stripe (international)
Payment states: PENDING -> PROCESSING -> PAID | FAILED | REFUNDED

## TEST COMMANDS
```bash
uv run pytest -v                          # run all tests
uv run pytest tests/modules/test_auth.py  # single module
uv run ruff check . --fix                 # lint + autofix
uv run mypy src/                          # type check
uv run alembic upgrade head               # apply migrations
uv run alembic revision --autogenerate -m "name"  # new migration
uv run python -c "from src.main import app; print('OK')"  # import check
```

## FRONTEND STANDARDS
All API calls go through src/lib/api/client.ts — never raw fetch in components
Auth token: httpOnly cookie via Next.js API route (never localStorage)
Cart state: Zustand store persisted to localStorage
Server state: TanStack Query (all API calls, caching, optimistic updates)
Forms: React Hook Form + Zod validation
Every page: loading state + error state + empty state handled
Mobile-first responsive (Tailwind breakpoints: sm/md/lg/xl)

## BOT STANDARDS (Aiogram3)
Bot talks to backend ONLY via httpx -> REST API
AuthMiddleware on every update (sync user with backend)
ThrottlingMiddleware: max 30 req/min per user
FSM states for: checkout flow, address input
All keyboards in keyboards/inline.py or keyboards/reply.py
No business logic in handlers — call services/api_client.py

## PROJECT STATUS
[LAST UPDATED: manually update this before each session]
DONE: auth, users, catalog, inventory, cart, orders, payments, shipping, reviews, vendors, notifications, tasks, admin, main.py (app factory), tests, bot
CURRENT: frontend
NEXT: infra
TOOLING: backend/manage.py CLI (interactive menu + subcommands); alembic ruff post-write hook fixed; alembic env.py render_item fixes JSONB/Text autogen

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
