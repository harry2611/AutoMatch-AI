"use client";

import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ShieldCheck } from "lucide-react";

import { MetricCard } from "@/components/metric-card";
import { SectionCard } from "@/components/section-card";
import { fetchDealerDashboard, formatCurrency, formatPercent, login } from "@/lib/api";
import type { DealerDashboardResponse } from "@/lib/types";

export default function DealerPage() {
  const [email, setEmail] = useState("dealer@automatch.ai");
  const [password, setPassword] = useState("demo1234");
  const [token, setToken] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DealerDashboardResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const auth = await login(email, password);
      setToken(auth.access_token);
      const nextDashboard = await fetchDealerDashboard(auth.access_token);
      setDashboard(nextDashboard);
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Unable to load dealer dashboard.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-10 lg:px-10">
      <section className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
        <SectionCard
          title="Dealer dashboard"
          subtitle="Log in with the seeded dealer account to inspect likely-to-convert leads, demand heat, pricing gaps, and response-time impact."
        >
          <div className="rounded-[24px] border border-brand-100 bg-brand-50 p-5 text-sm text-brand-900">
            Demo credentials: <span className="font-semibold">dealer@automatch.ai / demo1234</span>
          </div>
          <div className="mt-5 grid gap-4">
            <div>
              <label className="label" htmlFor="dealer-email">Email</label>
              <input id="dealer-email" className="field" value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="dealer-password">Password</label>
              <input
                id="dealer-password"
                type="password"
                className="field"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>
            <button type="button" className="button-primary gap-2" disabled={loading} onClick={handleLogin}>
              <ShieldCheck className="h-4 w-4" />
              {loading ? "Loading..." : token ? "Refresh dashboard" : "Load dashboard"}
            </button>
            {error ? <p className="text-sm text-red-700">{error}</p> : null}
          </div>
        </SectionCard>

        <SectionCard
          title={dashboard ? dashboard.dealer.name : "Dealer intelligence surface"}
          subtitle="Quality score, response rate, and close efficiency update from the same event stream that powers buyer ranking."
        >
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Quality Score"
              value={dashboard ? formatPercent(dashboard.dealer.quality_score) : "0.0%"}
              hint="Composite of close rate, response rate, and response speed."
            />
            <MetricCard
              label="Response Rate"
              value={dashboard ? formatPercent(dashboard.dealer.response_rate) : "0.0%"}
              hint="Share of dealer responses on incoming lead actions."
            />
            <MetricCard
              label="Avg Response Time"
              value={dashboard ? `${dashboard.dealer.average_response_minutes.toFixed(0)}m` : "0m"}
              hint="Faster response keeps Bayesian dealer quality elevated."
            />
            <MetricCard
              label="High-Intent Leads"
              value={dashboard ? String(dashboard.high_intent_leads.length) : "0"}
              hint="Recent buyers ordered by posterior purchase probability."
            />
          </div>

          <div className="mt-6 rounded-[24px] border border-slate-100 bg-slate-50 p-5 text-sm leading-7 text-slate-600">
            {dashboard
              ? `The live dealer view is authenticated with the backend token and scoped to ${dashboard.dealer.city}, ${dashboard.dealer.state}.`
              : "Authenticate to load the dealer-scoped dashboard."}
          </div>
        </SectionCard>
      </section>

      {dashboard ? (
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <SectionCard title="High-intent leads" subtitle="Likely-to-convert buyers currently clustering around your inventory.">
            <div className="space-y-3">
              {dashboard.high_intent_leads.map((lead, index) => (
                <div key={`${lead.buyer_id}-${lead.vehicle_label}-${index}`} className="rounded-2xl border border-slate-100 bg-white px-4 py-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-lg font-semibold text-ink">{lead.buyer_name}</p>
                      <p className="text-sm text-slate-600">
                        Budget up to {formatCurrency(lead.budget_max)} for {lead.vehicle_label}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Posterior</p>
                      <p className="mt-1 text-xl font-semibold text-brand-900">{formatPercent(lead.purchase_probability)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Vehicle demand" subtitle="Clicks, saves, and test-drive requests stacked by vehicle.">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dashboard.vehicle_demand}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="clicks" stackId="a" fill="#8DA35A" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="saves" stackId="a" fill="#0F8B8D" />
                  <Bar dataKey="test_drive_requests" stackId="a" fill="#E67E22" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>

          <SectionCard title="Close-rate trend" subtitle="Recommendations vs conversions over the last 14 daily snapshots.">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dashboard.close_rate_trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="recommendation_count" fill="#CBD5E1" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="conversion_count" fill="#4C6431" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </SectionCard>

          <SectionCard title="Pricing gaps + response impact" subtitle="Where your pricing is rich or discounted relative to the market, plus the conversion effect of dealer latency buckets.">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-[24px] border border-slate-100 bg-white p-4">
                <p className="text-sm font-semibold text-ink">Pricing gaps</p>
                <div className="mt-3 space-y-3">
                  {dashboard.pricing_gaps.map((gap) => (
                    <div key={gap.vehicle_id} className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                      <div className="flex items-center justify-between gap-3">
                        <span>{gap.label}</span>
                        <span className={gap.gap_amount <= 0 ? "font-semibold text-brand-900" : "font-semibold text-orange-700"}>
                          {gap.gap_amount <= 0 ? "Below market" : "Above market"} {formatCurrency(Math.abs(gap.gap_amount))}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-[24px] border border-slate-100 bg-white p-4">
                <p className="text-sm font-semibold text-ink">Response-time impact</p>
                <div className="mt-3 space-y-3">
                  {dashboard.response_time_impact.map((bucket) => (
                    <div key={bucket.bucket} className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                      <div className="flex items-center justify-between gap-3">
                        <span>{bucket.bucket}</span>
                        <span className="font-semibold text-ink">{formatPercent(bucket.conversion_rate)}</span>
                      </div>
                      <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-500">
                        {bucket.recommendation_count} scored recommendations
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </SectionCard>
        </div>
      ) : null}
    </main>
  );
}

