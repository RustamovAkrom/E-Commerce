"use client";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface StarRatingInputProps {
  rating: number;
  onRatingChange?: (rating: number) => void;
  readonly?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "size-4",
  md: "size-5",
  lg: "size-6",
};

export function StarRatingInput({
  rating,
  onRatingChange,
  readonly = false,
  size = "md",
  className,
}: StarRatingInputProps) {
  if (readonly) {
    return (
      <div className={cn("flex gap-1", className)}>
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={cn(
              sizeClasses[size],
              star <= rating
                ? "fill-yellow-400 text-yellow-400"
                : "fill-transparent text-gray-300",
            )}
          />
        ))}
      </div>
    );
  }

  return (
    <div className={cn("flex gap-1", className)}>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => onRatingChange?.(star)}
          className="transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded"
          aria-label={`Rate ${star} stars`}
        >
          <Star
            className={cn(
              sizeClasses[size],
              star <= rating
                ? "fill-yellow-400 text-yellow-400"
                : "fill-transparent text-gray-300",
              "transition-colors",
            )}
          />
        </button>
      ))}
    </div>
  );
}
