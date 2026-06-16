"use client";
import { ErrorMessage } from "@/components/common/error-message";
export default function ErrorPage({ error, reset }: { error: Error; reset: () => void }) { return <div className="mx-auto max-w-3xl px-4 py-16"><ErrorMessage message={error.message} retry={reset} /></div>; }
