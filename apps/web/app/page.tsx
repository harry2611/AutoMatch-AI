import Link from "next/link";
import { Activity, ArrowRight, CarFront, ChartSpline, Gauge, Radar, Workflow } from "lucide-react";

const pillars = [
  {
    icon: Radar,
    title: "Bayesian match scoring",
    copy: "Posterior purchase probability updates in real time from clicks, saves, rejects, and test-drive intent.",
  },
  {
    icon: Gauge,
    title: "Revenue-aware ranking",
    copy: "Every recommendation balances close likelihood, dealer quality, commission opportunity, inventory health, and distance.",
  },
  {
    icon: Workflow,
    title: "Full marketplace feedback loop",
    copy: "Buyer experiences, dealer dashboards, experiment controls, and analytics all share one PostgreSQL event backbone.",
  },
];

const stack = [
  "Next.js + TypeScript + Tailwind",
  "FastAPI + SQLAlchemy + PostgreSQL",
  "Redis + APScheduler",
  "NumPy + pandas + scikit-learn",
  "Dockerized local development",
];

export default function HomePage() {
  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-10 px-6 py-10 lg:px-10">
      <section className="panel overflow-hidden">
        <div className="grid gap-10 bg-hero-grid px-8 py-12 lg:grid-cols-[1.15fr_0.85fr] lg:px-12">
          <div>
            <span className="kicker">Marketplace intelligence for modern auto retail</span>
            <h1 className="mt-5 max-w-4xl text-5xl font-semibold leading-tight text-ink lg:text-6xl">
              AutoMatch AI turns noisy browsing signals into ranked buyer-to-vehicle matches that actually convert.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-700">
              A full-stack recommendation and experimentation platform for car marketplaces, blending Bayesian posteriors,
              dealer quality, distance, and revenue optimization into one explainable ranking engine.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/buyer" className="button-primary gap-2">
                Explore buyer app <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/dealer" className="button-secondary gap-2">
                Open dealer dashboard
              </Link>
              <Link href="/admin" className="button-secondary gap-2">
                Review experiments
              </Link>
            </div>
          </div>

          <div className="grid gap-4">
            <div className="rounded-[28px] bg-ink p-6 text-white shadow-panel">
              <div className="flex items-center gap-3">
                <ChartSpline className="h-5 w-5 text-brand-300" />
                <p className="text-sm uppercase tracking-[0.18em] text-brand-100">Live optimization loop</p>
              </div>
              <div className="mt-6 grid gap-4">
                <div className="rounded-2xl bg-white/10 p-4">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-300">Buyer signal</p>
                  <p className="mt-2 text-lg font-semibold">Search, click, save, reject, test drive</p>
                </div>
                <div className="rounded-2xl bg-white/10 p-4">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-300">Posterior update</p>
                  <p className="mt-2 text-lg font-semibold">Dealer, brand, body type, financing, urgency priors</p>
                </div>
                <div className="rounded-2xl bg-white/10 p-4">
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-300">Rank output</p>
                  <p className="mt-2 text-lg font-semibold">Probability + margin + distance + inventory + quality</p>
                </div>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-[28px] border border-orange-100 bg-orange-50 p-5">
                <p className="text-xs uppercase tracking-[0.18em] text-orange-700">Buyer surface</p>
                <p className="mt-3 text-xl font-semibold text-ink">Explainable recommendations with live reranking</p>
              </div>
              <div className="rounded-[28px] border border-brand-100 bg-brand-50 p-5">
                <p className="text-xs uppercase tracking-[0.18em] text-brand-900">Ops surface</p>
                <p className="mt-3 text-xl font-semibold text-ink">Dealer trends and A/B experiment governance</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-3">
        {pillars.map((pillar) => {
          const Icon = pillar.icon;
          return (
            <div key={pillar.title} className="panel p-6">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-900">
                <Icon className="h-5 w-5" />
              </div>
              <h2 className="mt-5 text-2xl font-semibold text-ink">{pillar.title}</h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">{pillar.copy}</p>
            </div>
          );
        })}
      </section>

      <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="panel p-7">
          <div className="flex items-center gap-3">
            <Activity className="h-5 w-5 text-ocean-700" />
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Operational surfaces</span>
          </div>
          <div className="mt-6 space-y-5">
            <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">
              <h3 className="text-xl font-semibold text-ink">Buyer app</h3>
              <p className="mt-2 text-sm text-slate-600">
                Capture budget, ZIP, financing preference, urgency, and brand/body affinities, then return ranked, explainable recommendations.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">
              <h3 className="text-xl font-semibold text-ink">Dealer IQ</h3>
              <p className="mt-2 text-sm text-slate-600">
                Surface high-intent leads, close-rate trends, pricing gaps, and the conversion impact of response speed.
              </p>
            </div>
            <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5">
              <h3 className="text-xl font-semibold text-ink">Experiment Lab</h3>
              <p className="mt-2 text-sm text-slate-600">
                Compare heuristic ranking vs Bayesian ranking on precision@k, conversion lift, revenue lift, CTR, and average distance.
              </p>
            </div>
          </div>
        </div>

        <div className="panel p-7">
          <div className="flex items-center gap-3">
            <CarFront className="h-5 w-5 text-accent-700" />
            <span className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Implementation stack</span>
          </div>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {stack.map((item) => (
              <div key={item} className="rounded-2xl border border-slate-100 bg-white px-4 py-4 text-sm font-semibold text-slate-700">
                {item}
              </div>
            ))}
          </div>
          <div className="mt-6 rounded-[24px] border border-brand-100 bg-brand-50 p-5">
            <p className="text-sm leading-7 text-brand-900">
              Seeded demo accounts: <span className="font-semibold">admin@automatch.ai / demo1234</span> and{" "}
              <span className="font-semibold">dealer@automatch.ai / demo1234</span>.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}

