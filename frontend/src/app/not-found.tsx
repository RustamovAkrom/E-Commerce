import Link from "next/link";
import { EmptyState } from "@/components/common/empty-state";
import { Button } from "@/components/ui/button";
export default function NotFound() { return <div className="mx-auto max-w-3xl px-4 py-16"><EmptyState title="Sahifa topilmadi" description="Manzilni tekshiring yoki bosh sahifaga qayting." action={<Button asChild><Link href="/">Bosh sahifa</Link></Button>} /></div>; }
