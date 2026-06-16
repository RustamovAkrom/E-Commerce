"use client";
import { Button } from "@/components/ui/button";
export function Pagination({ page, pages, onChange }: { page: number; pages: number; onChange: (page: number) => void }) { if (pages <= 1) return null; return <nav aria-label="Sahifalash" className="flex items-center justify-center gap-3"><Button variant="outline" disabled={page <= 1} onClick={() => onChange(page - 1)}>Oldingi</Button><span className="text-sm text-muted-foreground">{page} / {pages}</span><Button variant="outline" disabled={page >= pages} onClick={() => onChange(page + 1)}>Keyingi</Button></nav>; }
