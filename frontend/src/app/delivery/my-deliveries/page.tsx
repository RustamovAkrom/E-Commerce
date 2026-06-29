import type { Route } from "next";
import { redirect } from "next/navigation";

// Courier deliveries moved to the dedicated /courier dashboard.
export default function LegacyDeliveriesRedirect() {
  redirect("/courier" as Route);
}
