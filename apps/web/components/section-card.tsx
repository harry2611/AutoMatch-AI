import type { ReactNode } from "react";

interface SectionCardProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function SectionCard({ title, subtitle, children }: SectionCardProps) {
  return (
    <section className="panel p-6">
      <div className="mb-5">
        <h2 className="text-2xl font-semibold text-ink">{title}</h2>
        {subtitle ? <p className="mt-2 max-w-2xl text-sm text-slate-600">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}

