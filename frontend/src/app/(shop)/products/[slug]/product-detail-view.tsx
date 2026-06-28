"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ShoppingCart, MessageSquare } from "lucide-react";
import { toast } from "sonner";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { LoadingSpinner } from "@/components/common/loading-spinner";
import { ProductImages } from "@/components/product/product-images";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { productsApi } from "@/lib/api/products";
import { reviewsApi } from "@/lib/api/reviews";
import { useCartStore } from "@/lib/stores/cart.store";
import { useAuthStore } from "@/lib/stores/auth.store";
import { formatPrice } from "@/lib/utils";
import { RatingSummary } from "@/components/review/rating-summary";
import { ReviewList } from "@/components/review/review-list";
import { ReviewForm } from "@/components/review/review-form";
export function ProductDetailView({ slug }: { slug: string }) {
  const [reviewFormOpen, setReviewFormOpen] = useState(false);
  const user = useAuthStore((s) => s.user);
  
  const query = useQuery({
    queryKey: ["product", slug],
    queryFn: () => productsApi.detail(slug),
  });

  const ratingSummaryQuery = useQuery({
    queryKey: ["rating-summary", query.data?.id],
    queryFn: () => reviewsApi.productRatingSummary(query.data!.id),
    enabled: !!query.data?.id,
  });

  const add = useCartStore((s) => s.addItem);
  if (query.isLoading) return <LoadingSpinner className="min-h-[60vh]" />;
  if (query.error)
    return (
      <div className="mx-auto max-w-3xl px-4 py-12">
        <ErrorMessage
          message={query.error.message}
          retry={() => void query.refetch()}
        />
      </div>
    );
  if (!query.data) return <EmptyState title="Mahsulot topilmadi" />;
  const product = query.data;
  return (
    <>
    <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 md:grid-cols-2 animate-fade-in">
      <ProductImages images={product.images} name={product.name} />
      <div className="space-y-5">
        <Badge variant={product.stock ? "success" : "destructive"}>
          {product.stock ? `${product.stock} dona mavjud` : "Sotuvda yo‘q"}
        </Badge>
        <h1 className="text-3xl font-bold sm:text-4xl">{product.name}</h1>
        <p className="text-2xl font-black">
          {formatPrice(product.price, product.currency)}
        </p>
        <div className="flex items-center gap-4">
          <RatingSummary 
            summary={ratingSummaryQuery.data} 
            loading={ratingSummaryQuery.isLoading}
            size="lg"
          />
        </div>
        <p className="leading-7 text-muted-foreground">
          {product.description ?? "Mahsulot tavsifi kiritilmagan."}
        </p>
        <Button
          size="lg"
          disabled={!product.stock}
          onClick={() => {
            add(product);
            toast.success("Savatga qo‘shildi");
          }}
        >
          <ShoppingCart className="size-5" /> Savatga qo‘shish
        </Button>
        {product.attributes.length > 0 && (
          <>
            <Separator />
            <dl className="grid grid-cols-2 gap-3">
              {product.attributes.map((attribute) => (
                <div key={attribute.id} className="rounded-xl bg-muted p-3">
                  <dt className="text-xs text-muted-foreground">
                    {attribute.key}
                  </dt>
                  <dd className="font-medium">{attribute.value}</dd>
                </div>
              ))}
            </dl>
          </>
        )}
      </div>
    </div>

    {/* Reviews Section */}
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-12">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold sm:text-3xl">Sharhlar</h2>
          <RatingSummary 
            summary={ratingSummaryQuery.data} 
            loading={ratingSummaryQuery.isLoading}
            showCount
          />
        </div>
        {user && (
          <Button onClick={() => setReviewFormOpen(true)} className="gap-2">
            <MessageSquare className="size-4" />
            Sharh qoldirish
          </Button>
        )}
      </div>
      <Separator />
      <ReviewList productId={product.id} />
    </div>

    {/* Review Form Dialog */}
    <ReviewForm
      productId={product.id}
      open={reviewFormOpen}
      onOpenChange={setReviewFormOpen}
      onSuccess={() => {
        ratingSummaryQuery.refetch();
      }}
    />
    </>
  );
}
