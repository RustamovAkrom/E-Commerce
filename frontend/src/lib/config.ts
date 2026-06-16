export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  appName: process.env.NEXT_PUBLIC_APP_NAME ?? "E-Commerce",
  currency: process.env.NEXT_PUBLIC_CURRENCY ?? "UZS",
  locale: process.env.NEXT_PUBLIC_LOCALE ?? "uz-UZ",
  telegramBot: process.env.NEXT_PUBLIC_TELEGRAM_BOT ?? "",
  marketplaceMode: process.env.NEXT_PUBLIC_MARKETPLACE_MODE === "true",
} as const;

export const apiV1 = `${config.apiUrl}/api/v1`;
