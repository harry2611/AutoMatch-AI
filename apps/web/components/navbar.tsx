"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/buyer", label: "Buyer App" },
  { href: "/dealer", label: "Dealer IQ" },
  { href: "/admin", label: "Experiment Lab" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-white/60 bg-surface/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-10">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-700 text-sm font-bold text-white">
            AM
          </div>
          <div>
            <div className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">AutoMatch AI</div>
            <div className="text-base font-semibold text-ink">Bayesian marketplace optimizer</div>
          </div>
        </Link>

        <nav className="hidden items-center gap-2 rounded-full border border-white/70 bg-white/80 p-1 shadow-panel md:flex">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "rounded-full px-4 py-2 text-sm font-semibold transition",
                  active ? "bg-brand-700 text-white" : "text-slate-600 hover:text-brand-900",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}

