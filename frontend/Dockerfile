# ─── Build stage ────────────────────────────────────────────────────────────
FROM node:22-alpine AS builder

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Copy package files first (layer caching)
COPY package.json pnpm-lock.yaml ./

# Install production deps only
RUN pnpm install --frozen-lockfile --prod

# Copy source
COPY . .

# Build
RUN pnpm build

# ─── Production stage ───────────────────────────────────────────────────────
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy Next.js static assets
COPY --from=builder /app/public /usr/share/nginx/html
COPY --from=builder /app/.next/standalone /app
COPY --from=builder /app/.next/static /app/.next/static

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
