import { Boxes, Gauge, Store } from "lucide-react";
import { Sidebar } from "@/components/layout/sidebar";
import { RoleGuard } from "@/components/auth/role-guard";

// Vendor (seller) panel: storefront profile, own products and sales. Only the
// vendor role may enter.
export default function VendorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleGuard allow={["vendor"]}>
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 md:grid-cols-[240px_1fr]">
        <Sidebar
          title="Sotuvchi paneli"
          links={[
            { href: "/vendor", label: "Dashboard", icon: <Gauge className="size-4" /> },
            { href: "/vendor/products", label: "Mahsulotlarim", icon: <Boxes className="size-4" /> },
            { href: "/vendor/profile", label: "Do‘kon profili", icon: <Store className="size-4" /> },
          ]}
        />
        <div>{children}</div>
      </div>
    </RoleGuard>
  );
}
