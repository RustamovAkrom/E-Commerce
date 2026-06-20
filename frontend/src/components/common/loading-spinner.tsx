import { LoaderCircle } from "lucide-react";
import { cn } from "@/lib/utils";
export function LoadingSpinner({
  label = "Yuklanmoqda",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      role="status"
      className={cn(
        "flex min-h-40 flex-col items-center justify-center gap-3 text-muted-foreground",
        className,
      )}
    >
      <LoaderCircle className="size-7 animate-spin" />
      <span className="text-sm">{label}</span>
    </div>
  );
}
