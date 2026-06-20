import { CircleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
export function ErrorMessage({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex min-h-40 flex-col items-center justify-center gap-3 rounded-2xl border border-red-200 bg-red-50 p-6 text-center text-red-800"
    >
      <CircleAlert className="size-7" />
      <p>{message}</p>
      {retry && (
        <Button variant="outline" onClick={retry}>
          Qayta urinish
        </Button>
      )}
    </div>
  );
}
