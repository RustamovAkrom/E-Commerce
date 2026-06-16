import { type ClassValue, clsx } from "clsx";
import { config } from "@/lib/config";
import type { Money } from "@/types/api";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatPrice(amount: Money, currency = config.currency): string {
  return new Intl.NumberFormat(config.locale, {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(Number(amount));
}

export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return new Intl.DateTimeFormat(config.locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(d);
}
