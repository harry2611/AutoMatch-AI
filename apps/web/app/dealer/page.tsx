"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ShieldCheck, UserPlus } from "lucide-react";

import { MetricCard } from "@/components/metric-card";
import { SectionCard } from "@/components/section-card";
import { fetchDealerDashboard, fetchDealers, formatCurrency, formatPercent, login, signupDealer } from "@/lib/api";
import type { DealerDashboardResponse, DealerListItem } from "@/lib/types";

type AuthMode = "login" | "signup";
type SignupMode = "existing" | "new";

const initialSignupForm = {
  full_name: "",
  email: "",
  password: "",
  dealer_id: "",
  dealership_name: "",
  zip_code: "",
  city: "",
  state: "",
};

export default function DealerPage() {
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("dealer@automatch.ai");
  const [password, setPassword] = useState("demo1234");
  const [signupMode, setSignupMode] = useState<SignupMode>("existing");
  const [signupForm, setSignupForm] = useState(initialSignupForm);
  const [dealers, setDealers] = useState<DealerListItem[]>([]);
  const [dealersLoading, setDealersLoading] = useState(true);
  const [dealerListError, setDealerListError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DealerDashboardResponse | null>(null);
  const [statusMessage, setStatusMessage] = useState("Sign in with a dealer account or create one to open a dealership-scoped dashboard.");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadDealerOptions() {
      try {
        setDealerListError(null);
        const nextDealers = await fetchDealers();
        if (!active) return;
        setDealers(nextDealers);
        setSignupForm((current) => ({
          ...current,
          dealer_id: current.dealer_id || (nextDealers[0] ? String(nextDealers[0].id) : ""),
        }));
      } catch (fetchError) {
        if (!active) return;
        setDealerListError(fetchError instanceof Error ? fetchError.message : "Unable to load dealership options.");
      } finally {
        if (active) {
          setDealersLoading(false);
        }
      }
    }

    loadDealerOptions();
    return () => {
      active = false;
    };
  }, []);

  const loadDashboard = async (accessToken: string, nextStatus?: string) => {
    const nextDashboard = await fetchDealerDashboard(accessToken);
    setToken(accessToken);
    setDashboard(nextDashboard);
    setStatusMessage(
      nextStatus
        ?? `Authenticated for ${nextDashboard.dealer.name} in ${nextDashboard.dealer.city}, ${nextDashboard.dealer.state}.`,
    );
  };

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const auth = await login(email, password);
      await loadDashboard(auth.access_token, `Signed in as ${auth.user.full_name}.`);
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Unable to load dealer dashboard.");
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async () => {
    if (signupMode === "existing" && !signupForm.dealer_id) {
      setError("Select a dealership before creating the account.");
      return;
    }

    if (
      signupMode === "new"
      && (!signupForm.dealership_name.trim()
        || !signupForm.zip_code.trim()
        || !signupForm.city.trim()
        || !signupForm.state.trim())
    ) {
      setError("Enter the dealership name, ZIP code, city, and state to create a new dealership.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const payload =
        signupMode === "existing"
          ? {
              full_name: signupForm.full_name,
              email: signupForm.email,
              password: signupForm.password,
              dealer_id: Number(signupForm.dealer_id),
            }
          : {
              full_name: signupForm.full_name,
              email: signupForm.email,
              password: signupForm.password,
              dealership_name: signupForm.dealership_name,
              zip_code: signupForm.zip_code,
              city: signupForm.city,
              state: signupForm.state,
            };

      const auth = await signupDealer(payload);
      setEmail(signupForm.email);
      setPassword(signupForm.password);
      setMode("login");
      await loadDashboard(
        auth.access_token,
        signupMode === "existing"
          ? "Dealer account created and linked to the selected demo dealership."
          : "Dealer account created. Your new dealership dashboard is live and ready for inventory.",
      );
      setSignupForm((current) => ({
        ...initialSignupForm,
        dealer_id: current.dealer_id,
      }));
    } catch (signupError) {
      setError(signupError instanceof Error ? signupError.message : "Unable to create the dealer account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-10 lg:px-10">
      <section className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
        <SectionCard
          title="Dealer dashboard"
          subtitle="Use the seeded demo login or create a dealer account that can attach to an existing demo dealership or a brand-new dealership profile."
        >
          <div className="inline-flex rounded-full border border-slate-200 bg-white p-1">
            <button
              type="button"
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                mode === "login" ? "bg-brand-900 text-white" : "text-slate-600"
              }`}
              onClick={() => setMode("login")}
            >
              Sign in
            </button>
            <button
              type="button"
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                mode === "signup" ? "bg-brand-900 text-white" : "text-slate-600"
              }`}
              onClick={() => setMode("signup")}
            >
              Create account
            </button>
          </div>

          {mode === "login" ? (
            <div className="mt-5 grid gap-4">
              <div className="rounded-[24px] border border-brand-100 bg-brand-50 p-5 text-sm text-brand-900">
                Demo credentials: <span className="font-semibold">dealer@automatch.ai / demo1234</span>
              </div>
              <div>
                <label className="label" htmlFor="dealer-email">Email</label>
                <input id="dealer-email" type="email" className="field" value={email} onChange={(event) => setEmail(event.target.value)} />
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
            </div>
          ) : (
            <div className="mt-5 grid gap-4">
              <div className="rounded-[24px] border border-orange-100 bg-orange-50 p-5 text-sm leading-7 text-orange-900">
                Create a dealer account and either attach it to an existing demo dealership for instant data, or start a brand-new dealership profile.
              </div>
              <div>
                <label className="label" htmlFor="signup-name">Full name</label>
                <input
                  id="signup-name"
                  className="field"
                  value={signupForm.full_name}
                  onChange={(event) => setSignupForm((current) => ({ ...current, full_name: event.target.value }))}
                />
              </div>
              <div>
                <label className="label" htmlFor="signup-email">Email</label>
                <input
                  id="signup-email"
                  type="email"
                  className="field"
                  value={signupForm.email}
                  onChange={(event) => setSignupForm((current) => ({ ...current, email: event.target.value }))}
                />
              </div>
              <div>
                <label className="label" htmlFor="signup-password">Password</label>
                <input
                  id="signup-password"
                  type="password"
                  className="field"
                  value={signupForm.password}
                  onChange={(event) => setSignupForm((current) => ({ ...current, password: event.target.value }))}
                />
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <button
                  type="button"
                  className={`rounded-[22px] border px-4 py-3 text-left text-sm transition ${
                    signupMode === "existing"
                      ? "border-brand-200 bg-brand-50 text-brand-900"
                      : "border-slate-200 bg-white text-slate-600"
                  }`}
                  onClick={() => setSignupMode("existing")}
                >
                  <p className="font-semibold">Use existing demo dealership</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.16em]">Best for instant seeded dashboard data</p>
                </button>
                <button
                  type="button"
                  className={`rounded-[22px] border px-4 py-3 text-left text-sm transition ${
                    signupMode === "new"
                      ? "border-brand-200 bg-brand-50 text-brand-900"
                      : "border-slate-200 bg-white text-slate-600"
                  }`}
                  onClick={() => setSignupMode("new")}
                >
                  <p className="font-semibold">Create new dealership</p>
                  <p className="mt-1 text-xs uppercase tracking-[0.16em]">Starts with a clean, empty dashboard</p>
                </button>
              </div>

              {signupMode === "existing" ? (
                <div>
                  <label className="label" htmlFor="signup-dealer">Dealership</label>
                  <select
                    id="signup-dealer"
                    className="field"
                    value={signupForm.dealer_id}
                    disabled={dealersLoading || !dealers.length}
                    onChange={(event) => setSignupForm((current) => ({ ...current, dealer_id: event.target.value }))}
                  >
                    {dealers.map((dealer) => (
                      <option key={dealer.id} value={dealer.id}>
                        {dealer.name} · {dealer.city}, {dealer.state}
                      </option>
                    ))}
                  </select>
                  {dealersLoading ? <p className="mt-2 text-sm text-slate-500">Loading dealership options...</p> : null}
                  {dealerListError ? <p className="mt-2 text-sm text-red-700">{dealerListError}</p> : null}
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="md:col-span-2">
                    <label className="label" htmlFor="dealership-name">Dealership name</label>
                    <input
                      id="dealership-name"
                      className="field"
                      value={signupForm.dealership_name}
                      onChange={(event) => setSignupForm((current) => ({ ...current, dealership_name: event.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="label" htmlFor="dealership-zip">ZIP code</label>
                    <input
                      id="dealership-zip"
                      className="field"
                      value={signupForm.zip_code}
                      onChange={(event) => setSignupForm((current) => ({ ...current, zip_code: event.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="label" htmlFor="dealership-state">State</label>
                    <input
                      id="dealership-state"
                      className="field"
                      value={signupForm.state}
                      onChange={(event) => setSignupForm((current) => ({ ...current, state: event.target.value }))}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="label" htmlFor="dealership-city">City</label>
                    <input
                      id="dealership-city"
                      className="field"
                      value={signupForm.city}
                      onChange={(event) => setSignupForm((current) => ({ ...current, city: event.target.value }))}
                    />
                  </div>
                  <p className="md:col-span-2 text-sm text-slate-500">
                    New dealership signup currently supports the seeded California ZIP codes used in the demo dataset.
                  </p>
                </div>
              )}

              <button type="button" className="button-primary gap-2" disabled={loading} onClick={handleSignup}>
                <UserPlus className="h-4 w-4" />
                {loading ? "Creating account..." : "Create account and load dashboard"}
              </button>
            </div>
          )}

          {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}
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
            {statusMessage}
          </div>
        </SectionCard>
      </section>

      {dashboard ? (
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <SectionCard title="High-intent leads" subtitle="Likely-to-convert buyers currently clustering around your inventory.">
            {dashboard.high_intent_leads.length ? (
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
            ) : (
              <EmptyDealerState message="No high-intent leads yet. Once buyers interact with your inventory, likely-to-convert shoppers will appear here." />
            )}
          </SectionCard>

          <SectionCard title="Vehicle demand" subtitle="Clicks, saves, and test-drive requests stacked by vehicle.">
            {dashboard.vehicle_demand.length ? (
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
            ) : (
              <EmptyDealerState message="No vehicle demand data yet. Buyer clicks, saves, and test-drive requests will populate this chart." />
            )}
          </SectionCard>

          <SectionCard title="Close-rate trend" subtitle="Recommendations vs conversions over the last 14 daily snapshots.">
            {dashboard.close_rate_trend.length ? (
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
            ) : (
              <EmptyDealerState message="No recommendation history yet. Conversion trends will appear after the marketplace scores inventory for your dealership." />
            )}
          </SectionCard>

          <SectionCard title="Pricing gaps + response impact" subtitle="Where your pricing is rich or discounted relative to the market, plus the conversion effect of dealer latency buckets.">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-[24px] border border-slate-100 bg-white p-4">
                <p className="text-sm font-semibold text-ink">Pricing gaps</p>
                {dashboard.pricing_gaps.length ? (
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
                ) : (
                  <p className="mt-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    No inventory has been attached to this dealership yet, so pricing gaps are not available.
                  </p>
                )}
              </div>
              <div className="rounded-[24px] border border-slate-100 bg-white p-4">
                <p className="text-sm font-semibold text-ink">Response-time impact</p>
                {dashboard.response_time_impact.length ? (
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
                ) : (
                  <p className="mt-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    Response-time impact will appear after the dealership has recommendation and response activity.
                  </p>
                )}
              </div>
            </div>
          </SectionCard>
        </div>
      ) : null}
    </main>
  );
}

function EmptyDealerState({ message }: { message: string }) {
  return (
    <div className="rounded-[24px] border border-slate-100 bg-slate-50 px-5 py-10 text-center text-sm leading-7 text-slate-600">
      {message}
    </div>
  );
}
