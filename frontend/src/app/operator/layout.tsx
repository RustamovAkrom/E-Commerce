import { Boxes, Gauge, Tags } from "lucide-react";
import { Sidebar } from "@/components/layout/sidebar";
import { RoleGuard } from "@/components/auth/role-guard";

// Operator panel: catalog & inventory management (products, categories). Admins
// and superadmins may also enter to assist operators.
export default function OperatorLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleGuard allow={["operator", "admin", "superadmin"]}>
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 md:grid-cols-[240px_1fr]">
        <Sidebar
          title="Operator paneli"
          links={[
            { href: "/operator", label: "Dashboard", icon: <Gauge className="size-4" /> },
            { href: "/operator/products", label: "Mahsulotlar", icon: <Boxes className="size-4" /> },
            { href: "/operator/categories", label: "Kategoriyalar", icon: <Tags className="size-4" /> },
          ]}
        />
        <div>{children}</div>
      </div>
    </RoleGuard>
  );
}
