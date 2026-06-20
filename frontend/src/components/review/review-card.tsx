"use client";
import { Calendar, CheckCircle2, Clock, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { StarRatingInput } from "./star-rating-input";
import type { Review } from "@/types/api";
import { cn } from "@/lib/utils";

interface ReviewCardProps {
  review: Review;
  showApprovalStatus?: boolean;
  className?: string;
}

export function ReviewCard({
  review,
  showApprovalStatus = false,
  className,
}: ReviewCardProps) {
  const formattedDate = new Date(review.created_at).toLocaleDateString("uz-UZ", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <Card className={cn("animate-fade-in", className)}>
      <CardContent className="p-6 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground font-medium">
              <User className="size-5" />
            </div>
            <div>
              <div className="font-medium">Foydalanuvchi</div>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Calendar className="size-3" />
                {formattedDate}
              </div>
            </div>
          </div>
          {showApprovalStatus && (
            <Badge
              variant={review.is_approved ? "success" : "secondary"}
              className="gap-1"
            >
              {review.is_approved ? (
                <>
                  <CheckCircle2 className="size-3" /> Tasdiqlangan
                </>
              ) : (
                <>
                  <Clock className="size-3" /> Kutilmoqda
                </>
              )}
            </Badge>
          )}
        </div>

        <Separator />

        {/* Rating */}
        <StarRatingInput rating={review.rating} readonly size="sm" />

        {/* Title */}
        {review.title && (
          <h3 className="font-semibold text-lg">{review.title}</h3>
        )}

        {/* Comment */}
        {review.comment && (
          <p className="text-sm leading-relaxed text-muted-foreground">
            {review.comment}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
