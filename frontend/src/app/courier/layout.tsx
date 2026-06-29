import { Truck } from "lucide-react";
import { Sidebar } from "@/components/layout/sidebar";
import { RoleGuard } from "@/components/auth/role-guard";

// Courier panel: assigned deliveries with map navigation. Only couriers enter.
export default function CourierLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RoleGuard allow={["courier"]}>
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 md:grid-cols-[240px_1fr]">
        <Sidebar
          title="Kuryer paneli"
          links={[
            { href: "/courier", label: "Yetkazuvlarim", icon: <Truck className="size-4" /> },
          ]}
        />
        <div>{children}</div>
      </div>
    </RoleGuard>
  );
}
