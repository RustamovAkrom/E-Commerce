# Build Frontend — Next.js 14 App Router

## Context
Backend REST API is complete at http://localhost:8000
API docs: http://localhost:8000/api/docs

## Frontend lives at: frontend/
Package manager: pnpm (never npm, never yarn)
Language: TypeScript strict mode
Styling: Tailwind CSS v3 + shadcn/ui components
State: Zustand (client) + TanStack Query v5 (server)

## Build order (strict — each depends on previous)

### Phase 1: Foundation
1. `pnpm create next-app frontend --typescript --tailwind --app --src-dir`
2. Install: `pnpm add @tanstack/react-query zustand react-hook-form zod`
3. Install shadcn: `pnpm dlx shadcn@latest init`
4. Install shadcn components: button, input, card, badge, dialog, drawer,
   sheet, toast, skeleton, avatar, separator, dropdown-menu, select

### Phase 2: Type-safe API client
Create `src/lib/api/client.ts` — base fetch wrapper with:
- Auto-attach Authorization header from Zustand auth store
- 401 handling: attempt token refresh, retry once, then logout
- Type parameter: `fetchJson<T>(url, options): Promise<T>`

Create typed API modules:
- `src/lib/api/auth.ts`     (login, register, refresh, logout, me)
- `src/lib/api/products.ts` (list, detail, search, filter)
- `src/lib/api/cart.ts`     (get, add, remove, clear)
- `src/lib/api/orders.ts`   (create, list, detail)
- `src/lib/api/users.ts`    (profile, update, addresses)

### Phase 3: State stores
- `src/lib/stores/auth.store.ts`   (user, accessToken, isAuthenticated, login(), logout(), refresh())
- `src/lib/stores/cart.store.ts`   (items, total, addItem(), removeItem(), clear(), syncWithBackend())

### Phase 4: Shared components
Layout: Header (nav + cart icon + auth), Footer, Sidebar
Product: ProductCard, ProductGrid, ProductFilters, ProductImages
Cart: CartDrawer (slide-in sheet), CartItem, CartSummary
Common: LoadingSpinner, ErrorMessage, EmptyState, Pagination, Badge

### Phase 5: Pages (App Router)
```
src/app/
  layout.tsx (QueryProvider, AuthProvider, Toaster)
  page.tsx (Homepage: hero + featured products)
  (shop)/
    products/
      page.tsx (Product listing with filters + search)
      [slug]/page.tsx (Product detail: images, price, add to cart)
  (auth)/
    login/page.tsx (Login form)
    register/page.tsx (Register form)
  cart/page.tsx (Full cart page)
  checkout/
    page.tsx (Multi-step: address -> payment -> confirm)
  success/page.tsx (Order placed confirmation)
  account/
    layout.tsx (Account sidebar nav)
    page.tsx (Profile settings)
    orders/page.tsx (Order history + status badges)
    addresses/page.tsx (Saved addresses CRUD)
  admin/
    layout.tsx (Admin sidebar, require ADMIN role)
    page.tsx (Dashboard: stats cards)
    products/page.tsx (Products table + CRUD)
    orders/page.tsx (Orders table + status management)
```

### Phase 6: Auth flow
- Login/register forms with React Hook Form + Zod
- Access token stored in Zustand (memory only)
- Refresh token in httpOnly cookie via `/api/auth/` Next.js route
- `middleware.ts` — protect /account/* and /admin/* routes
- Auto-refresh token on 401

### Phase 7: Config / environment
```typescript
// src/lib/config.ts
export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
  appName: process.env.NEXT_PUBLIC_APP_NAME ?? 'E-Commerce',
  currency: process.env.NEXT_PUBLIC_CURRENCY ?? 'UZS',
  locale: process.env.NEXT_PUBLIC_LOCALE ?? 'uz',
  telegramBot: process.env.NEXT_PUBLIC_TELEGRAM_BOT ?? '',
  marketplaceMode: process.env.NEXT_PUBLIC_MARKETPLACE_MODE === 'true',
}
```

## Quality rules
- Every page: loading skeleton + error boundary + empty state
- Mobile-first (sm: md: lg: xl: breakpoints)
- No inline styles — Tailwind classes only
- All images: next/image with proper alt text
- All links: next/link (never <a> for internal)
- Accessibility: aria-label on icon buttons, proper heading hierarchy
