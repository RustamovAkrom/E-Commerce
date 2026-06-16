import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { formatPrice } from "@/lib/utils";
export function CartSummary({ total, currency, checkout = true }: { total: number; currency: string; checkout?: boolean }) { return <div className="space-y-4 rounded-2xl border bg-card p-5"><h2 className="text-lg font-semibold">Buyurtma xulosasi</h2><Separator /><div className="flex justify-between"><span>Jami</span><strong>{formatPrice(total, currency)}</strong></div>{checkout && <Button asChild size="lg" className="w-full"><Link href="/checkout">Rasmiylashtirish</Link></Button>}</div>; }
