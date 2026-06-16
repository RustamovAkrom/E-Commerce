import type { Route } from "next";
import Link from "next/link";
export interface SidebarLink { href: Route; label: string; icon?: React.ReactNode }
export function Sidebar({ title, links }: { title: string; links: SidebarLink[] }) { return <aside className="rounded-2xl border bg-card p-4"><h2 className="mb-4 font-semibold">{title}</h2><nav className="flex gap-2 overflow-x-auto md:flex-col">{links.map((link) => <Link key={link.href} href={link.href} className="flex shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-sm hover:bg-accent">{link.icon}{link.label}</Link>)}</nav></aside>; }
