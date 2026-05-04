"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { CheckCircle, LineChart, Sparkles, XCircle } from "lucide-react";

import { MetricCard } from "@/components/metric-card";
import { RecommendationCard } from "@/components/recommendation-card";
import { SectionCard } from "@/components/section-card";
import { fetchRecommendations, formatCurrency, formatPercent, trackEvent } from "@/lib/api";
import type { BodyType, EventType, FinancingPreference, RecommendationItem, RecommendationResponse, UrgencyLevel } from "@/lib/types";

const initialForm = {
  name: "Demo Buyer",
  zip_code: "94103",
  budget_min: 26000,
  budget_max: 38000,
  preferred_brand: "Honda",
  preferred_body_type: "suv" as BodyType,
  financing_preference: "loan" as FinancingPreference,
  urgency: "high" as UrgencyLevel,
  top_k: 5,
};

// Inline toast shown next to action buttons so the user gets feedback
// without having to scroll back up.
interface Toast {
  id: number;
  type: "success" | "error";
  message: string;
}

export default function BuyerPage() {
  const [form, setForm] = useState(initialForm);
  // Separate string states so the budget fields feel natural while typing.
  // The numeric form values are only updated when the user finishes editing (onBlur).
  const [budgetMinStr, setBudgetMinStr] = useState(String(initialForm.budget_min));
  const [budgetMaxStr, setBudgetMaxStr] = useState(String(initialForm.budget_max));
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [message, setMessage] = useState<string>("Live posterior updates will show here after each interaction.");
  const [error, setError] = useState<string | null>(null);
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [isPending, startTransition] = useTransition();
  const toastCounter = useRef(0);

  const addToast = (type: Toast["type"], message: string) => {
    const id = ++toastCounter.current;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  // Re-uses the same buyer across form resubmissions so posterior history is preserved.
  const loadRecommendations = (payload?: Partial<typeof initialForm> & { buyer_id?: number }) => {
    startTransition(async () => {
      try {
        setError(null);
        const next = await fetchRecommendations({
          ...form,
          // Pass the existing buyer_id when re-generating so the engine updates
          // the same buyer's preferences rather than creating a new anonymous one.
          ...(result && !payload?.buyer_id ? { buyer_id: result.buyer_id } : {}),
          ...payload,
        });
        setResult(next);
        setMessage(
          `Serving ${next.ranking_strategy} recommendations from ${next.experiment_name ?? "the active experiment"} with version ${next.recommendation_version}.`,
        );
      } catch (fetchError) {
        const msg = fetchError instanceof Error ? fetchError.message : "Unable to load recommendations.";
        setError(msg);
      }
    });
  };

  useEffect(() => {
    loadRecommendations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleTrack = async (eventType: EventType, item: RecommendationItem) => {
    if (!result) return;

    const actionKey = `${item.recommendation_id ?? item.vehicle_id}:${eventType}`;
    setActiveAction(actionKey);
    setError(null);

    try {
      const eventResponse = await trackEvent({
        buyer_id: result.buyer_id,
        vehicle_id: item.vehicle_id,
        dealer_id: item.dealer_id,
        recommendation_id: item.recommendation_id,
        event_type: eventType,
        experiment_arm: result.experiment_arm,
        rerank: true,
        top_k: form.top_k,
      });

      if (eventResponse.reranked_recommendations) {
        setResult(eventResponse.reranked_recommendations);
      }

      const posteriorMsg = `Dealer posterior: ${formatPercent(eventResponse.posterior_snapshot.dealer ?? 0)}. Market posterior: ${formatPercent(eventResponse.posterior_snapshot.market ?? 0)}.`;
      setMessage(`${eventResponse.message} ${posteriorMsg}`);
      addToast("success", `${eventType.replace(/_/g, " ")} recorded — rankings updated.`);
    } catch (trackError) {
      const msg = trackError instanceof Error ? trackError.message : "Unable to track the event.";
      setError(msg);
      addToast("error", msg);
    } finally {
      setActiveAction(null);
    }
  };

  return (
    <main className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-10 lg:px-10">
      {/* Fixed toast stack — bottom-right, always visible */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`flex items-center gap-3 rounded-2xl px-5 py-3 text-sm font-medium shadow-lg transition-all ${
              toast.type === "success"
                ? "bg-brand-900 text-white"
                : "bg-red-700 text-white"
            }`}
          >
            {toast.type === "success" ? (
              <CheckCircle className="h-4 w-4 shrink-0" />
            ) : (
              <XCircle className="h-4 w-4 shrink-0" />
            )}
            {toast.message}
          </div>
        ))}
      </div>

      <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <SectionCard
          title="Buyer-side matching"
          subtitle="Tune the buyer profile and watch the marketplace posterior re-rank vehicles and dealers in real time."
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="label" htmlFor="name">Buyer label</label>
              <input
                id="name"
                className="field"
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              />
            </div>
            <div>
              <label className="label" htmlFor="zip">ZIP code</label>
              <input
                id="zip"
                className="field"
                value={form.zip_code}
                onChange={(event) => setForm((current) => ({ ...current, zip_code: event.target.value }))}
              />
            </div>
            <div>
              <label className="label" htmlFor="budget-min">Budget min</label>
              <input
                id="budget-min"
                type="text"
                inputMode="numeric"
                className="field"
                value={budgetMinStr}
                onFocus={(e) => e.target.select()}
                onChange={(e) => setBudgetMinStr(e.target.value)}
                onBlur={() => {
                  const parsed = parseInt(budgetMinStr.replace(/\D/g, ""), 10);
                  const value = isNaN(parsed) ? 0 : parsed;
                  setBudgetMinStr(String(value));
                  setForm((current) => ({ ...current, budget_min: value }));
                }}
              />
            </div>
            <div>
              <label className="label" htmlFor="budget-max">Budget max</label>
              <input
                id="budget-max"
                type="text"
                inputMode="numeric"
                className="field"
                value={budgetMaxStr}
                onFocus={(e) => e.target.select()}
                onChange={(e) => setBudgetMaxStr(e.target.value)}
                onBlur={() => {
                  const parsed = parseInt(budgetMaxStr.replace(/\D/g, ""), 10);
                  const value = isNaN(parsed) ? 0 : parsed;
                  setBudgetMaxStr(String(value));
                  setForm((current) => ({ ...current, budget_max: value }));
                }}
              />
            </div>
            <div>
              <label className="label" htmlFor="brand">Preferred brand</label>
              <input
                id="brand"
                className="field"
                value={form.preferred_brand}
                onChange={(event) => setForm((current) => ({ ...current, preferred_brand: event.target.value }))}
              />
            </div>
            <div>
              <label className="label" htmlFor="body-type">Body type</label>
              <select
                id="body-type"
                className="field"
                value={form.preferred_body_type}
                onChange={(event) => setForm((current) => ({ ...current, preferred_body_type: event.target.value as BodyType }))}
              >
                <option value="suv">SUV</option>
                <option value="sedan">Sedan</option>
                <option value="ev">EV</option>
                <option value="truck">Truck</option>
                <option value="wagon">Wagon</option>
              </select>
            </div>
            <div>
              <label className="label" htmlFor="financing">Financing</label>
              <select
                id="financing"
                className="field"
                value={form.financing_preference}
                onChange={(event) => setForm((current) => ({ ...current, financing_preference: event.target.value as FinancingPreference }))}
              >
                <option value="loan">Loan</option>
                <option value="lease">Lease</option>
                <option value="cash">Cash</option>
              </select>
            </div>
            <div>
              <label className="label" htmlFor="urgency">Urgency</label>
              <select
                id="urgency"
                className="field"
                value={form.urgency}
                onChange={(event) => setForm((current) => ({ ...current, urgency: event.target.value as UrgencyLevel }))}
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button type="button" className="button-primary gap-2" disabled={isPending} onClick={() => loadRecommendations()}>
              <Sparkles className="h-4 w-4" />
              {isPending ? "Generating..." : "Generate ranked matches"}
            </button>
            {result && (
              <button
                type="button"
                className="button-secondary gap-2 text-sm"
                disabled={isPending}
                onClick={() => {
                  setResult(null);
                  setMessage("Live posterior updates will show here after each interaction.");
                  setForm(initialForm);
                  setBudgetMinStr(String(initialForm.budget_min));
                  setBudgetMaxStr(String(initialForm.budget_max));
                }}
              >
                Reset
              </button>
            )}
            <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600">
              Demo flow: click, save, reject, or request a test drive to trigger posterior updates.
            </div>
          </div>
        </SectionCard>

        <SectionCard
          title="Realtime rank telemetry"
          subtitle="Each recommendation blends Bayesian purchase probability, dealer quality, distance, inventory health, and projected marketplace revenue."
        >
          <div className="grid gap-4 md:grid-cols-2">
            <MetricCard
              label="Experiment Arm"
              value={result ? result.experiment_arm.toUpperCase() : "WAITING"}
              hint={result ? `Version ${result.recommendation_version}` : "Run the engine to assign a buyer to an experiment arm."}
            />
            <MetricCard
              label="Top Match Value"
              value={result?.recommendations[0] ? formatCurrency(result.recommendations[0].price) : "$0"}
              hint={result?.recommendations[0] ? result.recommendations[0].dealer_name : "Waiting for inventory candidates."}
            />
            <MetricCard
              label="Top Match Probability"
              value={result?.recommendations[0] ? formatPercent(result.recommendations[0].purchase_probability) : "0.0%"}
              hint="Posterior probability of converting this buyer-vehicle-dealer combination."
            />
            <MetricCard
              label="Projected Revenue"
              value={result?.recommendations[0] ? formatCurrency(result.recommendations[0].expected_revenue) : "$0"}
              hint="Expected commission-weighted value for the marketplace."
            />
          </div>

          <div className="mt-6 rounded-[24px] border border-brand-100 bg-brand-50 p-5 text-sm leading-7 text-brand-900">
            <div className="mb-2 flex items-center gap-2 font-semibold">
              <LineChart className="h-4 w-4" />
              Posterior status
            </div>
            <p>{message}</p>
            {error ? <p className="mt-3 text-red-700">{error}</p> : null}
          </div>
        </SectionCard>
      </section>

      <section className="space-y-6">
        {result?.recommendations?.length ? (
          result.recommendations.map((item) => (
            <RecommendationCard
              key={item.recommendation_id ?? item.vehicle_id}
              item={item}
              activeAction={activeAction}
              preferredBodyType={form.preferred_body_type}
              preferredBrand={form.preferred_brand}
              onTrack={handleTrack}
            />
          ))
        ) : (
          <div className="panel px-6 py-12 text-center text-slate-600">
            Recommendation results will appear here once the engine scores inventory against the buyer profile.
          </div>
        )}
      </section>
    </main>
  );
}
