"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Menu, X, ArrowRight } from "lucide-react";

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/buyer", label: "Buyer App" },
  { href: "/dealer", label: "Dealer IQ" },
  { href: "/admin", label: "Experiment Lab" },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-white/60 bg-surface/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-10">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3" onClick={() => setMobileOpen(false)}>
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-700 text-sm font-bold text-white shadow-sm">
            AM
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">AutoMatch AI</div>
            <div className="text-sm font-semibold text-ink">Bayesian marketplace optimizer</div>
          </div>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-1 rounded-full border border-white/70 bg-white/80 p-1 shadow-panel md:flex">
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

        {/* Desktop CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/buyer"
            className="button-primary gap-2 py-2 text-xs"
          >
            Try live demo <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:text-brand-700 md:hidden"
          onClick={() => setMobileOpen((prev) => !prev)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="border-t border-slate-100 bg-white/95 px-6 pb-6 pt-4 backdrop-blur md:hidden">
          <nav className="flex flex-col gap-1">
            {navItems.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={clsx(
                    "rounded-2xl px-4 py-3 text-sm font-semibold transition",
                    active ? "bg-brand-700 text-white" : "text-slate-700 hover:bg-slate-50",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <Link
            href="/buyer"
            onClick={() => setMobileOpen(false)}
            className="button-primary mt-4 w-full justify-center gap-2"
          >
            Try live demo <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      )}
    </header>
  );
}
