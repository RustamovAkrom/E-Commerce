import Link from "next/link";
import { config } from "@/lib/config";
export function Footer() {
  return (
    <footer className="mt-auto border-t bg-muted/40">
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 sm:grid-cols-3">
        <div>
          <p className="font-bold">{config.appName}</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Ishonchli va qulay onlayn xarid.
          </p>
        </div>
        <div className="space-y-2 text-sm">
          <p className="font-semibold">Xarid</p>
          <Link href="/products" className="block text-muted-foreground">
            Mahsulotlar
          </Link>
          <Link href="/cart" className="block text-muted-foreground">
            Savat
          </Link>
        </div>
        <div className="space-y-2 text-sm">
          <p className="font-semibold">Hisob</p>
          <Link href="/account" className="block text-muted-foreground">
            Profil
          </Link>
          <Link href="/account/orders" className="block text-muted-foreground">
            Buyurtmalar
          </Link>
        </div>
      </div>
    </footer>
  );
}
