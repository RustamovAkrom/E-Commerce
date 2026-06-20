import { PackageOpen } from "lucide-react";
export function EmptyState({
  title = "Ma’lumot topilmadi",
  description = "Hozircha bu bo‘limda ma’lumot yo‘q.",
  action,
}: {
  title?: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed p-6 text-center">
      <PackageOpen className="size-10 text-muted-foreground" />
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="max-w-md text-sm text-muted-foreground">{description}</p>
      {action}
    </div>
  );
}
