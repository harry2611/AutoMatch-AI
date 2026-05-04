import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Brain,
  CarFront,
  ChartSpline,
  CheckCircle,
  ChevronRight,
  Gauge,
  LineChart,
  Radar,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Workflow,
  Zap,
} from "lucide-react";

const pillars = [
  {
    icon: Radar,
    title: "Bayesian match scoring",
    copy: "Posterior purchase probability updates in real time from clicks, saves, rejects, and test-drive intent — every signal sharpens the next recommendation.",
  },
  {
    icon: Gauge,
    title: "Revenue-aware ranking",
    copy: "Every recommendation balances close likelihood, dealer quality, commission opportunity, inventory health, and distance into one unified score.",
  },
  {
    icon: Workflow,
    title: "Full marketplace feedback loop",
    copy: "Buyer experiences, dealer dashboards, experiment controls, and analytics all share one PostgreSQL event backbone with zero data silos.",
  },
];

const stats = [
  { value: "5×", label: "Ranking factors fused" },
  { value: "6", label: "Buyer signals tracked" },
  { value: "<50ms", label: "Re-ranking latency" },
  { value: "A/B", label: "Experiment governance" },
];

const steps = [
  {
    number: "01",
    title: "Buyer submits a profile",
    description:
      "Budget range, ZIP code, preferred brand, body type, financing preference, and urgency level are captured and validated in a single request.",
  },
  {
    number: "02",
    title: "Engine scores every candidate",
    description:
      "The Bayesian engine blends purchase probability, dealer quality, inventory score, distance penalty, and expected commission into a unified ranking score.",
  },
  {
    number: "03",
    title: "Rankings adapt from every signal",
    description:
      "Each click, save, reject, or test-drive request updates the Beta-distribution priors for that buyer's segments, and re-ranks the remaining matches in real time.",
  },
];

const capabilities = [
  {
    icon: Brain,
    title: "Explainable AI",
    description: "Every recommendation ships with a plain-English reason list — buyers understand why a match appeared, not just that it did.",
  },
  {
    icon: TrendingUp,
    title: "Conversion lift measurement",
    description: "The Experiment Lab tracks Bayesian vs heuristic arms across CTR, precision@5, conversion rate, and commission-weighted revenue.",
  },
  {
    icon: ShieldCheck,
    title: "Authenticated dealer access",
    description: "JWT-gated dealer dashboards show high-intent leads, close-rate trends, pricing gaps, and the conversion impact of response speed.",
  },
  {
    icon: Zap,
    title: "Real-time posterior updates",
    description: "APScheduler refreshes dealer quality scores and caches analytics snapshots every 10 minutes — rankings stay current without blocking requests.",
  },
  {
    icon: BarChart3,
    title: "Pricing gap intelligence",
    description: "Dealers see exactly where their inventory sits relative to the market median for each brand and body type segment.",
  },
  {
    icon: LineChart,
    title: "Daily performance series",
    description: "Admin analytics surface daily CTR and conversion rate trends per experiment arm, plotted as a 14-day area chart.",
  },
];

const surfaces = [
  {
    label: "Buyer App",
    href: "/buyer",
    tag: "Live demo",
    description:
      "Submit a buyer profile and watch ranked, explainable recommendations appear — then click, save, or reject to see posteriors update in real time.",
    cta: "Try the buyer app",
    color: "orange",
  },
  {
    label: "Dealer IQ",
    href: "/dealer",
    tag: "Authenticated",
    description:
      "Log in as a dealer to see high-intent leads, vehicle demand charts, close-rate trends, pricing gaps, and response-time impact on conversions.",
    cta: "Open Dealer IQ",
    color: "brand",
  },
  {
    label: "Experiment Lab",
    href: "/admin",
    tag: "Admin only",
    description:
      "Compare heuristic vs Bayesian ranking on precision@5, CTR, revenue lift, and conversion lift — with full A/B experiment governance.",
    cta: "View Experiment Lab",
    color: "ocean",
  },
];

export default function HomePage() {
  return (
    <>
      <main className="mx-auto flex max-w-7xl flex-col gap-12 px-6 py-10 lg:px-10">

        {/* ── Hero ── */}
        <section className="panel overflow-hidden">
          <div className="grid gap-10 bg-hero-grid px-8 py-14 lg:grid-cols-[1.15fr_0.85fr] lg:px-12">
            <div>
              <span className="kicker">Marketplace intelligence for modern auto retail</span>
              <h1 className="mt-5 max-w-4xl text-5xl font-semibold leading-tight text-ink lg:text-6xl">
                Turn browsing signals into ranked matches that actually convert.
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-700">
                AutoMatch AI is a full-stack recommendation and experimentation platform for car marketplaces —
                blending Bayesian posteriors, dealer quality, distance, and revenue optimization into one
                explainable, real-time ranking engine.
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <Link href="/buyer" className="button-primary gap-2">
                  Try live demo <ArrowRight className="h-4 w-4" />
                </Link>
                <Link href="/dealer" className="button-secondary gap-2">
                  Dealer IQ
                </Link>
                <Link href="/admin" className="button-secondary gap-2">
                  Experiment Lab
                </Link>
              </div>

              <div className="mt-8 flex flex-wrap items-center gap-5 text-sm text-slate-500">
                <span className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-brand-700" /> No setup required</span>
                <span className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-brand-700" /> Seeded demo data</span>
                <span className="flex items-center gap-2"><CheckCircle className="h-4 w-4 text-brand-700" /> Real-time ranking</span>
              </div>
            </div>

            <div className="grid gap-4">
              <div className="rounded-[28px] bg-ink p-6 text-white shadow-panel">
                <div className="flex items-center gap-3">
                  <ChartSpline className="h-5 w-5 text-brand-300" />
                  <p className="text-sm uppercase tracking-[0.18em] text-brand-100">Live optimization loop</p>
                </div>
                <div className="mt-6 grid gap-3">
                  {[
                    { label: "Buyer signal", value: "Search · Click · Save · Reject · Test drive" },
                    { label: "Posterior update", value: "Dealer · Brand · Body type · Financing · Urgency" },
                    { label: "Rank output", value: "Probability × margin × distance × inventory × quality" },
                  ].map((row) => (
                    <div key={row.label} className="rounded-2xl bg-white/10 p-4">
                      <p className="text-xs uppercase tracking-[0.16em] text-slate-300">{row.label}</p>
                      <p className="mt-2 text-base font-semibold">{row.value}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-[28px] border border-orange-100 bg-orange-50 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-orange-700">Buyer surface</p>
                  <p className="mt-3 text-lg font-semibold text-ink">Explainable recommendations with live re-ranking</p>
                </div>
                <div className="rounded-[28px] border border-brand-100 bg-brand-50 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-brand-900">Ops surface</p>
                  <p className="mt-3 text-lg font-semibold text-ink">Dealer trends and A/B experiment governance</p>
                </div>
              </div>
            </div>
          </div>

          {/* Stats bar */}
          <div className="grid grid-cols-2 divide-x divide-slate-100 border-t border-slate-100 lg:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.label} className="px-8 py-6 text-center">
                <p className="text-3xl font-semibold text-ink">{stat.value}</p>
                <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">{stat.label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Core pillars ── */}
        <section className="grid gap-6 lg:grid-cols-3">
          {pillars.map((pillar) => {
            const Icon = pillar.icon;
            return (
              <div key={pillar.title} className="panel p-7 transition hover:shadow-lg">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-900">
                  <Icon className="h-5 w-5" />
                </div>
                <h2 className="mt-5 text-xl font-semibold text-ink">{pillar.title}</h2>
                <p className="mt-3 text-sm leading-7 text-slate-600">{pillar.copy}</p>
              </div>
            );
          })}
        </section>

        {/* ── How it works ── */}
        <section className="panel overflow-hidden p-8 lg:p-12">
          <div className="mb-10 flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-brand-700" />
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">How it works</span>
          </div>
          <div className="grid gap-8 lg:grid-cols-3">
            {steps.map((step, i) => (
              <div key={step.number} className="flex gap-5">
                <div className="flex flex-col items-center">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-700 text-sm font-bold text-white">
                    {step.number}
                  </div>
                  {i < steps.length - 1 && (
                    <div className="mt-3 hidden h-full w-px bg-gradient-to-b from-brand-200 to-transparent lg:block" />
                  )}
                </div>
                <div className="pb-6">
                  <h3 className="text-lg font-semibold text-ink">{step.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-slate-600">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Platform surfaces ── */}
        <section>
          <div className="mb-6 flex items-center gap-3">
            <Activity className="h-5 w-5 text-ocean-700" />
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Platform surfaces</span>
          </div>
          <div className="grid gap-6 lg:grid-cols-3">
            {surfaces.map((surface) => {
              const tagColor =
                surface.color === "orange"
                  ? "border-orange-200 bg-orange-50 text-orange-700"
                  : surface.color === "ocean"
                  ? "border-teal-200 bg-teal-50 text-teal-700"
                  : "border-brand-200 bg-brand-50 text-brand-900";
              return (
                <div key={surface.label} className="panel flex flex-col p-7">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-xl font-semibold text-ink">{surface.label}</h3>
                    <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${tagColor}`}>
                      {surface.tag}
                    </span>
                  </div>
                  <p className="mt-4 flex-1 text-sm leading-7 text-slate-600">{surface.description}</p>
                  <Link
                    href={surface.href}
                    className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-brand-700 hover:text-brand-900"
                  >
                    {surface.cta} <ChevronRight className="h-4 w-4" />
                  </Link>
                </div>
              );
            })}
          </div>
        </section>

        {/* ── Platform capabilities ── */}
        <section className="panel p-8 lg:p-12">
          <div className="mb-8 flex items-center gap-3">
            <CarFront className="h-5 w-5 text-accent-700" />
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Platform capabilities</span>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {capabilities.map((cap) => {
              const Icon = cap.icon;
              return (
                <div key={cap.title} className="rounded-[24px] border border-slate-100 bg-slate-50 p-5">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white shadow-sm">
                    <Icon className="h-4 w-4 text-brand-700" />
                  </div>
                  <h4 className="mt-4 text-base font-semibold text-ink">{cap.title}</h4>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{cap.description}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* ── CTA banner ── */}
        <section className="overflow-hidden rounded-[28px] bg-ink px-8 py-14 text-white lg:px-14">
          <div className="flex flex-col items-start justify-between gap-8 lg:flex-row lg:items-center">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-300">Ready to explore?</p>
              <h2 className="mt-3 max-w-xl text-3xl font-semibold leading-snug lg:text-4xl">
                See the Bayesian ranking engine in action with live demo data.
              </h2>
            </div>
            <div className="flex shrink-0 flex-col gap-3 sm:flex-row">
              <Link href="/buyer" className="button-primary gap-2 bg-brand-500 hover:bg-brand-400">
                Launch buyer app <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/admin"
                className="inline-flex items-center justify-center gap-2 rounded-full border border-white/30 bg-white/10 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/20"
              >
                View experiment results
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ── */}
      <footer className="mt-8 border-t border-slate-200/60 bg-white/40 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-6 py-10 text-sm text-slate-500 lg:flex-row lg:px-10">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-700 text-xs font-bold text-white">AM</div>
            <span className="font-semibold text-ink">AutoMatch AI</span>
            <span className="text-slate-300">·</span>
            <span>Bayesian marketplace optimizer</span>
          </div>
          <nav className="flex flex-wrap items-center justify-center gap-6">
            <Link href="/buyer" className="hover:text-brand-700 transition">Buyer App</Link>
            <Link href="/dealer" className="hover:text-brand-700 transition">Dealer IQ</Link>
            <Link href="/admin" className="hover:text-brand-700 transition">Experiment Lab</Link>
          </nav>
          <p className="text-xs text-slate-400">© {new Date().getFullYear()} AutoMatch AI. Built with FastAPI, Next.js &amp; PostgreSQL.</p>
        </div>
      </footer>
    </>
  );
}
