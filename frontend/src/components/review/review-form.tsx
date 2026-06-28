"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { reviewsApi } from "@/lib/api/reviews";
import { StarRatingInput } from "./star-rating-input";
import type { ReviewCreate } from "@/types/api";

const reviewSchema = z.object({
  rating: z.number().min(1, "Baholash shart").max(5, "Maksimal 5 yulduz"),
  title: z.string().min(3, "Sarlavha kamida 3 belgi").max(255, "Sarlavha 255 belgidan oshmasin").optional().or(z.literal("")),
  comment: z.string().min(10, "Izoh kamida 10 belgi").max(4000, "Izoh 4000 belgidan oshmasin").optional().or(z.literal("")),
});

type ReviewFormData = z.infer<typeof reviewSchema>;

interface ReviewFormProps {
  productId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  existingReview?: ReviewCreate;
  onSuccess?: () => void;
}

export function ReviewForm({
  productId,
  open,
  onOpenChange,
  existingReview,
  onSuccess,
}: ReviewFormProps) {
  const [rating, setRating] = useState(existingReview?.rating ?? 0);
  const client = useQueryClient();

  const form = useForm<ReviewFormData>({
    resolver: zodResolver(reviewSchema),
    defaultValues: {
      rating: existingReview?.rating ?? 0,
      title: existingReview?.title ?? "",
      comment: existingReview?.comment ?? "",
    },
  });

  const mutation = useMutation({
    mutationFn: (data: ReviewCreate) => reviewsApi.createReview(productId, data),
    onSuccess: () => {
      toast.success("Sharh muvaffaqiyatli qo'shildi");
      form.reset();
      setRating(0);
      onOpenChange(false);
      client.invalidateQueries({ queryKey: ["product-reviews", productId] });
      client.invalidateQueries({ queryKey: ["rating-summary", productId] });
      onSuccess?.();
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const onSubmit = (data: ReviewFormData) => {
    mutation.mutate({
      rating,
      title: data.title || null,
      comment: data.comment || null,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Star className="size-5 fill-yellow-400 text-yellow-400" />
            Sharh qoldirish
          </DialogTitle>
        </DialogHeader>
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              {/* Rating */}
              <div className="space-y-2">
                <label className="block text-sm font-medium">
                  Baholash <span className="text-destructive">*</span>
                </label>
                <div className="flex items-center gap-4">
                  <StarRatingInput
                    rating={rating}
                    onRatingChange={setRating}
                    size="lg"
                  />
                  {rating > 0 && (
                    <span className="text-sm font-medium text-muted-foreground">
                      {rating}/5
                    </span>
                  )}
                </div>
                {form.formState.errors.rating && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.rating.message}
                  </p>
                )}
              </div>

              {/* Title */}
              <div className="space-y-2">
                <label className="block text-sm font-medium">
                  Sarlavha
                </label>
                <Input
                  {...form.register("title")}
                  placeholder="Sharhingiz sarlavhasi"
                />
                {form.formState.errors.title && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.title.message}
                  </p>
                )}
              </div>

              {/* Comment */}
              <div className="space-y-2">
                <label className="block text-sm font-medium">
                  Izoh
                </label>
                <textarea
                  {...form.register("comment")}
                  placeholder="Mahsulot haqida o'z fikringizni yozing..."
                  className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
                {form.formState.errors.comment && (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.comment.message}
                  </p>
                )}
              </div>

              <Button
                type="submit"
                disabled={mutation.isPending || rating === 0}
                className="w-full gap-2"
              >
                {mutation.isPending && <Loader2 className="size-4 animate-spin" />}
                {mutation.isPending ? "Yuborilmoqda..." : "Sharhni yuborish"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </DialogContent>
    </Dialog>
  );
}
