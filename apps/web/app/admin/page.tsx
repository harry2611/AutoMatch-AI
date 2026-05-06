"use client";

import { useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { FlaskConical } from "lucide-react";

import { MetricCard } from "@/components/metric-card";
import { SectionCard } from "@/components/section-card";
import { fetchAnalytics, fetchExperimentDashboard, formatCompact, formatCurrency, formatPercent, login } from "@/lib/api";
import type { AnalyticsOverviewResponse, ExperimentDashboardResponse } from "@/lib/types";

export default function AdminPage() {
  const [email, setEmail] = useState("admin@automatch.ai");
  const [password, setPassword] = useState("demo1234");
  const [analytics, setAnalytics] = useState<AnalyticsOverviewResponse | null>(null);
  const [experiments, setExperiments] = useState<ExperimentDashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const auth = await login(email, password);
      const [nextAnalytics, nextExperiments] = await Promise.all([
        fetchAnalytics(auth.access_token),
        fetchExperimentDashboard(auth.access_token),
      ]);
      setAnalytics(nextAnalytics);
      setExperiments(nextExperiments);
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Unable to load admin analytics.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-10 lg:px-10">
      <section className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
        <SectionCard
          title="Admin experimentation lab"
          subtitle="Authenticate as the seeded admin to inspect the heuristic-vs-Bayesian experiment and outcome metrics. Public signup is intentionally disabled for admin access."
        >
          <div className="rounded-[24px] border border-orange-100 bg-orange-50 p-5 text-sm text-orange-900">
            Demo credentials: <span className="font-semibold">admin@automatch.ai / demo1234</span>
          </div>
          <div className="mt-5 grid gap-4">
            <div>
              <label className="label" htmlFor="admin-email">Email</label>
              <input id="admin-email" className="field" value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="admin-password">Password</label>
              <input
                id="admin-password"
                type="password"
                className="field"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>
            <button type="button" className="button-primary gap-2" disabled={loading} onClick={handleLogin}>
              <FlaskConical className="h-4 w-4" />
              {loading ? "Loading..." : "Load analytics"}
            </button>
            {error ? <p className="text-sm text-red-700">{error}</p> : null}
          </div>
        </SectionCard>

        <SectionCard
          title={experiments?.active_experiment?.name ?? "Experiment governance"}
          subtitle="A/B assignment, KPI lift, and daily trend visibility for ranking strategy changes."
        >
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Conversion Lift"
              value={analytics ? formatPercent(analytics.conversion_lift) : "0.0%"}
              hint="Bayesian arm vs heuristic arm."
            />
            <MetricCard
              label="Revenue Lift"
              value={analytics ? formatPercent(analytics.revenue_lift) : "0.0%"}
              hint="Commission-weighted lift attributable to ranking."
            />
            <MetricCard
              label="Avg Match Distance"
              value={analytics ? `${analytics.average_match_distance.toFixed(1)} mi` : "0.0 mi"}
              hint="Marketplace efficiency vs buyer convenience."
            />
            <MetricCard
              label="Experiment Count"
              value={experiments ? String(experiments.experiments.length) : "0"}
              hint="Total experiments currently stored in PostgreSQL."
            />
          </div>

          <div className="mt-6 rounded-[24px] border border-slate-100 bg-slate-50 p-5 text-sm leading-7 text-slate-600">
            {experiments?.active_experiment
              ? `${experiments.active_experiment.description} Treatment traffic split is ${(experiments.active_experiment.traffic_split * 100).toFixed(0)}%.`
              : "Authenticate to inspect the active experiment and KPI lift."}
          </div>
        </SectionCard>
      </section>

      {analytics ? (
        <div className="grid gap-6 lg:grid-cols-[1.08fr_0.92fr]">
          <SectionCard title="Headline metrics" subtitle="Resume-ready KPIs directly sourced from the analytics API.">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {analytics.headline_metrics.map((metric) => (
                <MetricCard
                  key={metric.name}
                  label={metric.label}
                  value={
                    metric.label.includes("Lift") || metric.label.includes("CTR") || metric.label.includes("Precision")
                      ? formatPercent(metric.value)
                      : formatCompact(metric.value)
                  }
                  hint={metric.name}
                />
              ))}
            </div>

            <div className="mt-6 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analytics.daily_series}>
                  <defs>
                    <linearGradient id="bayesFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4C6431" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#4C6431" stopOpacity={0.04} />
                    </linearGradient>
                    <linearGradient id="heuristicFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#E67E22" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#E67E22" stopOpacity={0.04} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="bayesian_conversion_rate" stroke="#4C6431" fill="url(#bayesFill)" />
                  <Area type="monotone" dataKey="heuristic_conversion_rate" stroke="#E67E22" fill="url(#heuristicFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>

          <SectionCard title="Arm comparison" subtitle="Bayesian and heuristic performance broken out across precision, revenue, distance, and dealer response rate.">
            <div className="space-y-4">
              {analytics.arms.map((arm) => (
                <div key={arm.arm} className="rounded-[24px] border border-slate-100 bg-white p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Arm</p>
                      <h3 className="mt-2 text-2xl font-semibold text-ink">{arm.arm.toUpperCase()}</h3>
                    </div>
                    <div className="rounded-full bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700">
                      Revenue {formatCurrency(arm.total_revenue)}
                    </div>
                  </div>
                  <div className="mt-5 grid gap-3 md:grid-cols-2">
                    <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">CTR: {formatPercent(arm.ctr)}</div>
                    <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">Precision@5: {formatPercent(arm.precision_at_k)}</div>
                    <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">Conversion rate: {formatPercent(arm.conversion_rate)}</div>
                    <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">Dealer response rate: {formatPercent(arm.dealer_response_rate)}</div>
                    <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">Avg distance: {arm.average_distance.toFixed(1)} miles</div>
                    <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">Revenue: {formatCurrency(arm.total_revenue)}</div>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      ) : null}
    </main>
  );
}
