import { EmptyState } from "@/components/common/empty-state";
import { ErrorMessage } from "@/components/common/error-message";
import { ProductCard } from "@/components/product/product-card";
import { Skeleton } from "@/components/ui/skeleton";
import type { Product } from "@/types/api";
export function ProductGrid({ products, loading, error, retry }: { products?: Product[]; loading?: boolean; error?: string | null; retry?: () => void }) {
  if (loading) return <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">{Array.from({ length: 8 }, (_, i) => <Skeleton key={i} className="aspect-[3/4]" shimmer />)}</div>;
  if (error) return <ErrorMessage message={error} retry={retry} />;
  if (!products?.length) return <EmptyState title="Mahsulot topilmadi" description="Filtrlarni o'zgartirib yana qidirib ko'ring." />;
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
      {products.map((product, i) => (
        <div key={product.id} className={`animate-slide-up animate-stagger-${Math.min(i + 1, 6)}`}>
          <ProductCard product={product} />
        </div>
      ))}
    </div>
  );
}
