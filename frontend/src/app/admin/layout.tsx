import { Boxes, Gauge, ShoppingCart, Store, Tags, Truck, Users } from "lucide-react";
import { Sidebar } from "@/components/layout/sidebar";
import { RoleGuard } from "@/components/auth/role-guard";

// Admin panel: full back-office (analytics, catalog, orders, users, vendors,
// couriers). Only admin and superadmin may enter.
export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleGuard allow={["admin", "superadmin"]}>
    <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 md:grid-cols-[240px_1fr]">
      <Sidebar
        title="Admin panel"
        links={[
          { href: "/admin", label: "Dashboard", icon: <Gauge className="size-4" /> },
          { href: "/admin/products", label: "Mahsulotlar", icon: <Boxes className="size-4" /> },
          { href: "/admin/categories", label: "Kategoriyalar", icon: <Tags className="size-4" /> },
          { href: "/admin/orders", label: "Buyurtmalar", icon: <ShoppingCart className="size-4" /> },
          { href: "/admin/users", label: "Foydalanuvchilar", icon: <Users className="size-4" /> },
          { href: "/admin/vendors", label: "Sotuvchilar", icon: <Store className="size-4" /> },
          { href: "/admin/couriers", label: "Kuryerlar", icon: <Truck className="size-4" /> },
        ]}
      />
      <div>{children}</div>
    </div>
    </RoleGuard>
  );
}
