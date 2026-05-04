import { BadgeDollarSign, CarFront, Clock3, Heart, Loader2, MapPin, MousePointerClick, ThumbsDown } from "lucide-react";

import { formatCurrency, formatPercent } from "@/lib/api";
import type { BodyType, EventType, RecommendationItem } from "@/lib/types";

interface RecommendationCardProps {
  item: RecommendationItem;
  activeAction?: string | null;
  preferredBodyType?: BodyType | string;
  preferredBrand?: string;
  onTrack: (eventType: EventType, item: RecommendationItem) => void;
}

export function RecommendationCard({ item, activeAction, preferredBodyType, preferredBrand, onTrack }: RecommendationCardProps) {
  const actionKey = (eventType: EventType) => `${item.recommendation_id ?? item.vehicle_id}:${eventType}`;
  const isAnyActionPending = activeAction !== null && activeAction !== undefined;

  const bodyMismatch = preferredBodyType && item.body_type !== preferredBodyType;
  const brandMismatch = preferredBrand && item.brand.toLowerCase() !== preferredBrand.toLowerCase();

  return (
    <article className="panel overflow-hidden">
      <div className="border-b border-slate-100 bg-gradient-to-r from-brand-50 via-white to-orange-50 px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="kicker">Rank #{item.rank}</div>
              {bodyMismatch && (
                <span className="rounded-full border border-orange-200 bg-orange-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-orange-700">
                  {item.body_type} · not your preferred type
                </span>
              )}
              {brandMismatch && !bodyMismatch && (
                <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                  {item.brand} · not your preferred brand
                </span>
              )}
            </div>
            <h3 className="mt-3 text-2xl font-semibold text-ink">
              {item.year} {item.brand} {item.model}
            </h3>
            <p className="mt-2 max-w-2xl text-sm text-slate-600">{item.explanation_text}</p>
          </div>
          <div className="rounded-[24px] bg-white/90 px-5 py-4 text-right shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Purchase Probability</p>
            <p className="mt-2 text-3xl font-semibold text-brand-900">{formatPercent(item.purchase_probability)}</p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 px-6 py-6 lg:grid-cols-[1.3fr_0.7fr]">
        <div className="space-y-4">
          <div className="flex flex-wrap gap-3 text-sm text-slate-600">
            <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-2">
              <CarFront className="h-4 w-4" /> {item.body_type.toUpperCase()} / {item.condition}
            </span>
            <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-2">
              <MapPin className="h-4 w-4" /> {item.distance_miles.toFixed(1)} miles
            </span>
            <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-2">
              <BadgeDollarSign className="h-4 w-4" /> {formatCurrency(item.price)}
            </span>
            <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-2">
              <Clock3 className="h-4 w-4" /> {item.dealer_name}
            </span>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {item.explanation.map((reason) => (
              <div key={reason} className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                {reason}
              </div>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            {item.features.map((feature) => (
              <span key={feature} className="rounded-full border border-brand-100 bg-brand-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-brand-900">
                {feature}
              </span>
            ))}
          </div>
        </div>

        <div className="rounded-[24px] border border-slate-100 bg-slate-50 p-5">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Expected Revenue</p>
              <p className="mt-2 text-xl font-semibold text-ink">{formatCurrency(item.expected_revenue)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Ranking Score</p>
              <p className="mt-2 text-xl font-semibold text-ink">{formatPercent(item.ranking_score)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Dealer Quality</p>
              <p className="mt-2 text-xl font-semibold text-ink">{formatPercent(item.dealer_quality)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Inventory Score</p>
              <p className="mt-2 text-xl font-semibold text-ink">{formatPercent(item.inventory_score)}</p>
            </div>
          </div>

          <div className="mt-5 grid gap-3">
            <ActionButton
              label="Track Click"
              pendingLabel="Updating..."
              icon={<MousePointerClick className="h-4 w-4" />}
              isPrimary
              isActive={activeAction === actionKey("click")}
              isDisabled={isAnyActionPending}
              onClick={() => onTrack("click", item)}
            />
            <ActionButton
              label="Save Match"
              pendingLabel="Saving..."
              icon={<Heart className="h-4 w-4" />}
              isActive={activeAction === actionKey("save")}
              isDisabled={isAnyActionPending}
              onClick={() => onTrack("save", item)}
            />
            <ActionButton
              label="Request Test Drive"
              pendingLabel="Requesting..."
              icon={<CarFront className="h-4 w-4" />}
              isActive={activeAction === actionKey("test_drive_request")}
              isDisabled={isAnyActionPending}
              onClick={() => onTrack("test_drive_request", item)}
            />
            <ActionButton
              label="Reject"
              pendingLabel="Rejecting..."
              icon={<ThumbsDown className="h-4 w-4" />}
              isActive={activeAction === actionKey("reject")}
              isDisabled={isAnyActionPending}
              onClick={() => onTrack("reject", item)}
            />
          </div>
        </div>
      </div>
    </article>
  );
}

// Small helper so each button shows a spinner when it's the active one,
// and is greyed-out (but not hidden) when another action is pending.
function ActionButton({
  label,
  pendingLabel,
  icon,
  isPrimary,
  isActive,
  isDisabled,
  onClick,
}: {
  label: string;
  pendingLabel: string;
  icon: React.ReactNode;
  isPrimary?: boolean;
  isActive: boolean;
  isDisabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className={`${isPrimary ? "button-primary" : "button-secondary"} gap-2 transition-opacity ${isDisabled && !isActive ? "opacity-50" : ""}`}
      disabled={isDisabled}
      onClick={onClick}
    >
      {isActive ? <Loader2 className="h-4 w-4 animate-spin" /> : icon}
      {isActive ? pendingLabel : label}
    </button>
  );
}
