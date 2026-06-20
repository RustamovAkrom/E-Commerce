import { House, MapPin, Package } from "lucide-react";
import { Sidebar } from "@/components/layout/sidebar";
export default function AccountLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 md:grid-cols-[240px_1fr]">
      <Sidebar
        title="Shaxsiy kabinet"
        links={[
          {
            href: "/account",
            label: "Profil",
            icon: <House className="size-4" />,
          },
          {
            href: "/account/orders",
            label: "Buyurtmalar",
            icon: <Package className="size-4" />,
          },
          {
            href: "/account/addresses",
            label: "Manzillar",
            icon: <MapPin className="size-4" />,
          },
        ]}
      />
      <div>{children}</div>
    </div>
  );
}
