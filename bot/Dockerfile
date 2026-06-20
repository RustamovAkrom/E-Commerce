# ─── Build stage ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

# Copy dependency files (package=false, so no readme needed for build)
COPY pyproject.toml uv.lock ./

# Install production deps into .venv
RUN uv sync --locked --no-dev

# ─── Production stage ───────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

# Copy bot source (run as module: python -m bot.main from /app)
COPY . ./bot

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "-m", "bot.main"]
