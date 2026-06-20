import Link from "next/link";
import { CircleCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
export default async function SuccessPage({
  searchParams,
}: {
  searchParams: Promise<{ order?: string | string[] }>;
}) {
  const params = await searchParams;
  const order = typeof params.order === "string" ? params.order : null;
  return (
    <div className="mx-auto flex min-h-[65vh] max-w-xl flex-col items-center justify-center gap-5 px-4 text-center animate-scale-in">
      <CircleCheck className="size-20 text-emerald-600" />
      <h1 className="text-3xl font-bold">Buyurtma qabul qilindi</h1>
      <p className="text-muted-foreground">
        {order
          ? `Buyurtma raqami: ${order}`
          : "Buyurtmangiz muvaffaqiyatli yaratildi."}
      </p>
      <div className="flex gap-3">
        <Button asChild>
          <Link href="/account/orders">Buyurtmalarim</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/products">Xaridni davom ettirish</Link>
        </Button>
      </div>
    </div>
  );
}
