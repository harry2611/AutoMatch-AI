"use client";

import { useRef, useState, useTransition } from "react";
import { CheckCircle, LineChart, Sparkles, XCircle } from "lucide-react";

import { MetricCard } from "@/components/metric-card";
import { RecommendationCard } from "@/components/recommendation-card";
import { SectionCard } from "@/components/section-card";
import { fetchRecommendations, formatCurrency, formatPercent, trackEvent } from "@/lib/api";
import type { BodyType, EventType, FinancingPreference, RecommendationItem, RecommendationResponse, UrgencyLevel } from "@/lib/types";

type BuyerForm = {
  name: string;
  zip_code: string;
  budget_min: number | null;
  budget_max: number | null;
  preferred_brand: string;
  preferred_body_type: BodyType | "";
  financing_preference: FinancingPreference | "";
  urgency: UrgencyLevel | "";
  top_k: number;
};

const emptyForm: BuyerForm = {
  name: "",
  zip_code: "",
  budget_min: null,
  budget_max: null,
  preferred_brand: "",
  preferred_body_type: "",
  financing_preference: "",
  urgency: "",
  top_k: 5,
};

const demoForm: BuyerForm = {
  name: "Demo Buyer",
  zip_code: "94103",
  budget_min: 26000,
  budget_max: 38000,
  preferred_brand: "Honda",
  preferred_body_type: "suv",
  financing_preference: "loan",
  urgency: "high",
  top_k: 5,
};

const initialStatusMessage = "Enter your preferences to generate personalized buyer-to-vehicle matches.";

// Inline toast shown next to action buttons so the user gets feedback
// without having to scroll back up.
interface Toast {
  id: number;
  type: "success" | "error";
  message: string;
}

export default function BuyerPage() {
  const [form, setForm] = useState<BuyerForm>(emptyForm);
  // Separate string states so the budget fields feel natural while typing.
  // The numeric form values are only updated when the user finishes editing (onBlur).
  const [budgetMinStr, setBudgetMinStr] = useState("");
  const [budgetMaxStr, setBudgetMaxStr] = useState("");
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [message, setMessage] = useState<string>(initialStatusMessage);
  const [error, setError] = useState<string | null>(null);
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [isPending, startTransition] = useTransition();
  const toastCounter = useRef(0);
  const hasFormInput = Boolean(
    form.name.trim()
    || form.zip_code.trim()
    || budgetMinStr
    || budgetMaxStr
    || form.preferred_brand.trim()
    || form.preferred_body_type
    || form.financing_preference
    || form.urgency,
  );

  const addToast = (type: Toast["type"], message: string) => {
    const id = ++toastCounter.current;
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  const syncForm = (nextForm: BuyerForm) => {
    setForm(nextForm);
    setBudgetMinStr(nextForm.budget_min !== null ? String(nextForm.budget_min) : "");
    setBudgetMaxStr(nextForm.budget_max !== null ? String(nextForm.budget_max) : "");
  };

  const validateForm = (candidate: BuyerForm) => {
    if (!candidate.zip_code.trim()) {
      return "Enter a 5-digit ZIP code to score nearby inventory.";
    }
    if (!/^\d{5}$/.test(candidate.zip_code.trim())) {
      return "ZIP code must be a 5-digit US ZIP code.";
    }
    if (candidate.budget_min === null || candidate.budget_max === null) {
      return "Enter both a minimum and maximum budget.";
    }
    if (candidate.budget_min < 0 || candidate.budget_max < 0) {
      return "Budget values must be non-negative.";
    }
    if (candidate.budget_min >= candidate.budget_max) {
      return "Budget min must be less than budget max.";
    }
    if (!candidate.preferred_body_type) {
      return "Select the body type you want to shop for.";
    }
    if (!candidate.financing_preference) {
      return "Choose a financing preference before generating matches.";
    }
    if (!candidate.urgency) {
      return "Choose an urgency level so the engine can score intent correctly.";
    }
    return null;
  };

  const buildPayload = (
    candidate: BuyerForm,
    options?: { buyer_id?: number; preserveExistingBuyer?: boolean },
  ) => {
    const preserveExistingBuyer = options?.preserveExistingBuyer ?? true;
    const buyerId = options?.buyer_id ?? (preserveExistingBuyer && result ? result.buyer_id : undefined);

    return {
      ...(buyerId ? { buyer_id: buyerId } : {}),
      ...(candidate.name.trim() ? { name: candidate.name.trim() } : {}),
      zip_code: candidate.zip_code.trim(),
      budget_min: candidate.budget_min ?? undefined,
      budget_max: candidate.budget_max ?? undefined,
      ...(candidate.preferred_brand.trim() ? { preferred_brand: candidate.preferred_brand.trim() } : {}),
      preferred_body_type: candidate.preferred_body_type as BodyType,
      financing_preference: candidate.financing_preference as FinancingPreference,
      urgency: candidate.urgency as UrgencyLevel,
      top_k: candidate.top_k,
    };
  };

  // Re-uses the same buyer across form resubmissions so posterior history is preserved.
  const loadRecommendations = (candidate: BuyerForm, options?: { buyer_id?: number; preserveExistingBuyer?: boolean }) => {
    const validationError = validateForm(candidate);
    if (validationError) {
      setError(validationError);
      setMessage(initialStatusMessage);
      return;
    }

    startTransition(async () => {
      try {
        setError(null);
        const next = await fetchRecommendations(buildPayload(candidate, options));
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
          subtitle="Start with your own preferences, or load the sample buyer to see the marketplace posterior re-rank vehicles and dealers in real time."
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="label" htmlFor="name">Buyer label (optional)</label>
              <input
                id="name"
                className="field"
                value={form.name}
                placeholder="e.g. Harsh"
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              />
            </div>
            <div>
              <label className="label" htmlFor="zip">ZIP code</label>
              <input
                id="zip"
                className="field"
                value={form.zip_code}
                placeholder="94103"
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
                placeholder="26000"
                onFocus={(e) => e.target.select()}
                onChange={(e) => setBudgetMinStr(e.target.value)}
                onBlur={() => {
                  const parsed = parseInt(budgetMinStr.replace(/\D/g, ""), 10);
                  const value = isNaN(parsed) ? null : parsed;
                  setBudgetMinStr(value !== null ? String(value) : "");
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
                placeholder="38000"
                onFocus={(e) => e.target.select()}
                onChange={(e) => setBudgetMaxStr(e.target.value)}
                onBlur={() => {
                  const parsed = parseInt(budgetMaxStr.replace(/\D/g, ""), 10);
                  const value = isNaN(parsed) ? null : parsed;
                  setBudgetMaxStr(value !== null ? String(value) : "");
                  setForm((current) => ({ ...current, budget_max: value }));
                }}
              />
            </div>
            <div>
              <label className="label" htmlFor="brand">Preferred brand (optional)</label>
              <input
                id="brand"
                className="field"
                value={form.preferred_brand}
                placeholder="Honda"
                onChange={(event) => setForm((current) => ({ ...current, preferred_brand: event.target.value }))}
              />
            </div>
            <div>
              <label className="label" htmlFor="body-type">Body type</label>
              <select
                id="body-type"
                className="field"
                value={form.preferred_body_type}
                onChange={(event) => setForm((current) => ({ ...current, preferred_body_type: event.target.value as BuyerForm["preferred_body_type"] }))}
              >
                <option value="">Select body type</option>
                <option value="suv">SUV</option>
                <option value="sedan">Sedan</option>
                <option value="ev">EV</option>
                <option value="truck">Truck</option>
                <option value="coupe">Coupe</option>
                <option value="wagon">Wagon</option>
              </select>
            </div>
            <div>
              <label className="label" htmlFor="financing">Financing</label>
              <select
                id="financing"
                className="field"
                value={form.financing_preference}
                onChange={(event) => setForm((current) => ({ ...current, financing_preference: event.target.value as BuyerForm["financing_preference"] }))}
              >
                <option value="">Select financing</option>
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
                onChange={(event) => setForm((current) => ({ ...current, urgency: event.target.value as BuyerForm["urgency"] }))}
              >
                <option value="">Select urgency</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button type="button" className="button-primary gap-2" disabled={isPending} onClick={() => loadRecommendations(form)}>
              <Sparkles className="h-4 w-4" />
              {isPending ? "Generating..." : "Generate ranked matches"}
            </button>
            <button
              type="button"
              className="button-secondary gap-2 text-sm"
              disabled={isPending}
              onClick={() => {
                syncForm(demoForm);
                setMessage("Loading the sample buyer profile and generating demo matches.");
                loadRecommendations(demoForm, { preserveExistingBuyer: false });
              }}
            >
              Try demo profile
            </button>
            {(result || hasFormInput) && (
              <button
                type="button"
                className="button-secondary gap-2 text-sm"
                disabled={isPending}
                onClick={() => {
                  setResult(null);
                  setError(null);
                  setMessage(initialStatusMessage);
                  syncForm(emptyForm);
                }}
              >
                Reset
              </button>
            )}
            <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600">
              Fill in the required fields or use the demo profile to explore live posterior updates.
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
              hint={result ? `Version ${result.recommendation_version}` : "Generate matches to assign this buyer to an experiment arm."}
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
            Recommendation results will appear here after the buyer profile is completed and the ranking engine is run.
          </div>
        )}
      </section>
    </main>
  );
}
