"use client";
import { Star } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ProductRatingSummary } from "@/types/api";
import { cn } from "@/lib/utils";

interface RatingSummaryProps {
  summary: ProductRatingSummary | null | undefined;
  loading?: boolean;
  size?: "sm" | "md" | "lg";
  showCount?: boolean;
  className?: string;
}

const sizeClasses = {
  sm: "text-sm",
  md: "text-base",
  lg: "text-lg",
};

const iconSize = {
  sm: "size-4",
  md: "size-5",
  lg: "size-6",
};

export function RatingSummary({
  summary,
  loading = false,
  size = "md",
  showCount = true,
  className,
}: RatingSummaryProps) {
  if (loading) {
    return (
      <div className={cn("flex items-center gap-2 animate-pulse", className)}>
        <div className="h-4 w-4 rounded bg-muted" />
        <div className="h-4 w-16 rounded bg-muted" />
      </div>
    );
  }

  if (!summary || summary.review_count === 0) {
    return (
      <div className={cn("flex items-center gap-2 text-muted-foreground", className)}>
        <Star className={cn(iconSize[size], "fill-transparent")} />
        <span className={cn(sizeClasses[size])}>Hali sharh yo&apos;q</span>
      </div>
    );
  }

  const rating = summary.average_rating.toFixed(1);

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Star className={cn(iconSize[size], "fill-yellow-400 text-yellow-400")} />
      <span className={cn("font-semibold", sizeClasses[size])}>{rating}</span>
      {showCount && (
        <Badge variant="outline" className="text-xs">
          {summary.review_count} {summary.review_count === 1 ? "sharh" : "sharh"}
        </Badge>
      )}
    </div>
  );
}
