"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { Pagination } from "@/components/common/pagination";
import { ReviewCard } from "./review-card";
import { reviewsApi } from "@/lib/api/reviews";
import type { Review } from "@/types/api";

type ReviewSort = "newest" | "oldest" | "highest" | "lowest";

interface ReviewListProps {
  productId: string;
  showApprovalStatus?: boolean;
}

const sortOptions: { value: ReviewSort; label: string }[] = [
  { value: "newest", label: "Eng yangi" },
  { value: "oldest", label: "Eng eski" },
  { value: "highest", label: "Eng yuqori baholangan" },
  { value: "lowest", label: "Eng past baholangan" },
];

export function ReviewList({
  productId,
  showApprovalStatus = false,
}: ReviewListProps) {
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<ReviewSort>("newest");
  const pageSize = 5;

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["product-reviews", productId, page, sort],
    queryFn: () =>
      reviewsApi.listProductReviews(productId, {
        page,
        size: pageSize,
        sort: getSortParam(sort),
      }),
  });

  const sortedReviews = sortReviews(data?.items ?? [], sort);

  function getSortParam(sort: ReviewSort): string {
    switch (sort) {
      case "newest":
        return "-created_at";
      case "oldest":
        return "created_at";
      case "highest":
        return "-rating";
      case "lowest":
        return "rating";
      default:
        return "-created_at";
    }
  }

  function sortReviews(reviews: Review[], sort: ReviewSort): Review[] {
    const sorted = [...reviews];
    switch (sort) {
      case "newest":
        return sorted.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      case "oldest":
        return sorted.sort((a, b) => 
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );
      case "highest":
        return sorted.sort((a, b) => b.rating - a.rating);
      case "lowest":
        return sorted.sort((a, b) => a.rating - b.rating);
      default:
        return sorted;
    }
  }

  if (isLoading) return <LoadingSpinner />;
  if (error)
    return (
      <ErrorMessage
        message={error.message}
        retry={() => void refetch()}
      />
    );
  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        title="Hali sharhlar yo'q"
        description="Bu mahsulotga birinchi sharhni siz qoldiring!"
        icon={MessageSquare}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Sort Options */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Jami {data.total} sharh
        </p>
        <div className="flex items-center gap-2">
          {sortOptions.map((option) => (
            <Button
              key={option.value}
              variant={sort === option.value ? "default" : "outline"}
              size="sm"
              onClick={() => {
                setSort(option.value);
                setPage(1);
              }}
              className="gap-1"
            >
              {option.label}
              {sort === option.value && (
                sort === "newest" || sort === "highest" ? (
                  <ArrowDown className="size-3" />
                ) : (
                  <ArrowUp className="size-3" />
                )
              )}
            </Button>
          ))}
        </div>
      </div>

      {/* Reviews */}
      <div className="space-y-4">
        {sortedReviews.map((review) => (
          <ReviewCard
            key={review.id}
            review={review}
            showApprovalStatus={showApprovalStatus}
          />
        ))}
      </div>

      {/* Pagination */}
      {data.pages > 1 && (
        <Pagination
          currentPage={page}
          totalPages={data.pages}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
