# 🛒 E-Commerce Platform

Zamonaviy e-commerce platforma — backend (FastAPI), frontend (Next.js) va Telegram bot dan iborat.

## 📋 Content

- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Environment Setup](#-environment-setup)
- [Backend](#-backend)
- [Frontend](#-frontend)
- [Bot](#-bot)
- [Docker](#-docker)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

## 🏗 Architecture

```
┌─────────────┐     HTTPS      ┌──────────────┐
│   Browser   │ ◄────────────► │   Nginx      │
└─────────────┘                │  (Frontend)  │
                               └──────┬───────┘
                                      │ REST
                               ┌──────┴───────┐
                               │   FastAPI    │
                               │  (Backend)   │
                               └──┬───┬───┬──┘
                                  │   │   │
                        ┌─────────┘   │   └──────────┐
                        │             │              │
                  ┌─────┴─────┐  ┌───┴───┐   ┌──────┴──────┐
                  │ PostgreSQL│  │ Redis │   │   MinIO     │
                  └───────────┘  └───────┘   └─────────────┘
```

## 🛠 Tech Stack

| Layer      | Technology                                          |
|------------|-----------------------------------------------------|
| **Frontend** | Next.js 14, React 19, TypeScript, Tailwind CSS v4 |
|            | shadcn/ui, TanStack Query v5, Zustand              |
| **Backend**  | FastAPI, Python 3.12, SQLAlchemy 2 (async)         |
|            | PostgreSQL, Redis, MinIO (S3)                       |
| **Bot**      | Aiogram 3, httpx                                   |
| **Infra**    | Docker, Docker Compose, Nginx                      |

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/)
- [uv](https://docs.astral.sh/uv/) (for local dev without Docker)
- [Node.js 22+](https://nodejs.org/) + [pnpm](https://pnpm.io/) (for frontend local dev)

### One-command setup

```bash
# 1. Clone & setup
git clone <repo-url>
cd ecommerce-platform
cp .env.example .env          # edit .env for your needs
make install                  # install all dependencies
make dev                      # start all services via Docker
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## 🔧 Environment Setup

### Copy and configure

```bash
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY and BOT_TOKEN
```

### Local development (without Docker)

```bash
# Backend
cd backend && uv sync && uv run uvicorn src.main:app --reload

# Frontend
cd frontend && pnpm install && pnpm dev

# Bot
cd bot && uv sync && uv run python -m bot.main
```

## 🖥 Backend

### Project structure

```
backend/src/
├── main.py                  # App factory
├── config.py                # Settings (env-based)
├── models_registry.py       # All ORM models
├── models/                  # SQLAlchemy models
├── modules/                 # Feature modules
│   ├── auth/                # JWT auth (register, login, refresh)
│   ├── users/               # User CRUD
│   ├── catalog/             # Categories & Products
│   ├── inventory/           # Stock management
│   ├── cart/                # Redis-based cart
│   ├── orders/              # Order lifecycle
│   ├── payments/            # Click, Payme, Stripe
│   ├── shipping/            # Shipping methods
│   ├── reviews/             # Product reviews
│   ├── vendors/             # Marketplace vendors
│   ├── notifications/       # Email/SMS/Telegram
│   ├── tasks/               # Celery background tasks
│   └── admin/               # Admin dashboard API
├── core/                    # Shared infrastructure
│   ├── base_repository.py   # Generic CRUD repo
│   ├── dependencies.py      # DI providers
│   ├── exceptions.py        # App exceptions
│   ├── middleware.py        # CORS, timing, etc.
│   ├── pagination.py        # Page<T> pagination
│   ├── rate_limit.py        # slowapi limiter
│   ├── redis.py             # Redis client
│   └── schemas.py           # Base Pydantic schemas
└── utils/                   # Helpers
```

### Commands

```bash
cd backend

uv run uvicorn src.main:app --reload          # dev server
uv run alembic upgrade head                   # DB migrations
uv run alembic revision --autogenerate -m "msg"  # new migration
uv run pytest -v                              # tests
uv run ruff check . --fix                     # lint
uv run mypy src/                              # type check
```

### API Endpoints (67 routes)

| Prefix               | Method   | Description              | Auth     |
|----------------------|----------|--------------------------|----------|
| `/api/v1/auth`       | POST     | register, login, refresh | Public   |
| `/api/v1/users`      | GET/PATCH| admin user management    | Admin    |
| `/api/v1/users/me`   | GET/PATCH| current user profile     | User     |
| `/api/v1/catalog`    | GET      | categories, products     | Public   |
| `/api/v1/catalog`    | POST/PATCH/DELETE | product CRUD   | Admin    |
| `/api/v1/cart`        | GET/POST/DELETE | cart operations | User     |
| `/api/v1/orders`     | POST     | create from cart         | User     |
| `/api/v1/orders`     | GET      | my orders                | User     |
| `/api/v1/orders/{id}`| GET/PATCH| order detail + status    | Admin    |
| `/api/v1/payments`   | POST     | init payment             | User     |
| `/api/v1/shipping`   | GET      | available methods        | Public   |
| `/api/v1/admin`      | GET      | dashboard stats          | Admin    |

Full interactive docs: **http://localhost:8000/api/docs**

## 🎨 Frontend

### Project structure

```
frontend/src/
├── app/                     # Next.js App Router
│   ├── layout.tsx           # Root layout (providers, header, footer)
│   ├── page.tsx             # Homepage (hero + featured products)
│   ├── globals.css          # Design tokens + animations
│   ├── (shop)/              # Public pages
│   │   ├── products/        # Product listing + detail
│   ├── (auth)/              # Auth pages
│   │   ├── login/           # Login form
│   │   └── register/        # Register form
│   ├── cart/                # Cart page
│   ├── checkout/            # Multi-step checkout
│   ├── account/             # User account
│   │   ├── orders/          # Order history
│   │   └── addresses/       # Address management
│   ├── admin/               # Admin dashboard
│   │   ├── products/        # Product CRUD table
│   │   └── orders/          # Order management
│   ├── success/             # Order confirmation
│   └── api/                 # Next.js API routes (auth proxy)
├── components/
│   ├── layout/              # Header, Footer, Sidebar
│   ├── product/             # ProductCard, Grid, Filters, Images
│   ├── cart/                # CartDrawer, CartItem, Summary
│   ├── common/              # LoadingSpinner, ErrorMessage, etc.
│   ├── providers/           # QueryProvider, AuthProvider
│   └── ui/                  # shadcn/ui primitives
├── lib/
│   ├── design-system.ts     # Color tokens, spacing, animations
│   ├── config.ts            # App config
│   ├── api/                 # Typed API modules
│   │   ├── client.ts        # Base fetch (401 refresh + retry)
│   │   ├── auth.ts          # login, register, logout
│   │   ├── products.ts      # list, detail, CRUD
│   │   ├── cart.ts          # get, add, remove, clear
│   │   ├── orders.ts        # create, list, detail
│   │   └── users.ts         # profile, update
│   └── stores/              # Zustand stores
│       ├── auth.store.ts    # user, tokens, login/logout
│       └── cart.store.ts    # items, total, sync
└── types/
    └── api.ts               # All API TypeScript types
```

### Commands

```bash
cd frontend

pnpm install                     # install deps
pnpm dev                         # dev server (localhost:3000)
pnpm build                       # production build
pnpm lint                        # ESLint
pnpm typecheck                   # TypeScript type check
```

### Design System

All design tokens are in `src/lib/design-system.ts`:

- **Colors**: primary, secondary, accent, surface, muted, border (HSL)
- **Spacing**: xs(4px) → 2xl(40px)
- **Border Radius**: sm/md/lg/full
- **Shadows**: sm/md/lg/xl
- **Animations**: fade-in, slide-up, scale-in, shimmer, pulse-ring
- **Breakpoints**: sm(640px) → 2xl(1536px)

### Animations (CSS-only, no Framer Motion)

| Animation        | Duration | Use Case                      |
|------------------|----------|-------------------------------|
| `fade-in`        | 300ms    | Page transitions              |
| `slide-up`       | 400ms    | Page transitions              |
| `slide-in-right` | 350ms    | Toasts, Cart drawer           |
| `scale-in`       | 200ms    | Modals, Dropdowns             |
| `shimmer`        | 1.5s     | Loading skeletons             |
| `pulse-ring`     | 1.5s     | Cart badge, notifications     |

Apply via Tailwind classes: `animate-fade-in`, `animate-slide-up`, `animate-shimmer`, etc.

## 🤖 Bot

Telegram bot for order management.

```bash
cd bot
uv sync
uv run python -m bot.main
```

Bot features:
- Browse products
- Add to cart via messages
- Place orders
- Track order status
- Telegram auth login

## 🐳 Docker

### Development

```bash
make dev           # Start all services
make stop          # Stop all services
make logs          # Backend logs
make shell-backend # Bash inside backend container
make shell-db      # psql inside postgres
```

### Production

```bash
# Build and start in production mode
make prod

# Build images only
make build
```

### Docker services

| Service    | Port   | Description                    |
|------------|--------|--------------------------------|
| frontend   | 3000   | Next.js (dev) / Nginx (prod)  |
| backend    | 8000   | FastAPI REST API               |
| postgres   | 5432   | PostgreSQL 16                  |
| redis      | 6379   | Redis 7 (caching, sessions)   |
| minio      | 9000   | S3 storage API                 |
| minio-console | 9001 | MinIO web console             |

## 📚 API Documentation

Interactive Swagger UI: **http://localhost:8000/api/docs**

ReDoc alternative: **http://localhost:8000/api/redoc**

## 🧪 Quality

```bash
# Backend
make lint              # ruff check + autofix
make test              # pytest
make verify            # import check + frontend typecheck

# Frontend
pnpm lint              # ESLint
pnpm typecheck         # tsc --noEmit
```

## 📦 Deployment

### Prerequisites

1. Set all `.env` variables (see [.env.example](.env.example))
2. `SECRET_KEY` — at least 32 characters, generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
3. `BOT_TOKEN` — from @BotFather on Telegram
4. Domain and SSL certificate for Nginx

### Steps

```bash
# 1. Pull latest code
git pull

# 2. Copy .env (production values)
cp .env.production .env

# 3. Build and start
make build
make prod

# 4. Run migrations
docker-compose exec backend uv run alembic upgrade head
```

### Nginx SSL (optional)

Add to `frontend/nginx.conf`:
```nginx
listen 443 ssl;
ssl_certificate /etc/ssl/certs/domain.crt;
ssl_certificate_key /etc/ssl/private/domain.key;
```

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/name`
2. Follow [Backend](#-backend) and [Frontend](#-frontend) standards
3. Run `make lint` and `make test` before committing
4. Submit PR with description

## 📄 License

Private — E-Commerce Platform
