import { BadgeDollarSign, CarFront, Clock3, Heart, MapPin, MousePointerClick, ThumbsDown } from "lucide-react";

import { formatCurrency, formatPercent } from "@/lib/api";
import type { EventType, RecommendationItem } from "@/lib/types";

interface RecommendationCardProps {
  item: RecommendationItem;
  activeAction?: string | null;
  onTrack: (eventType: EventType, item: RecommendationItem) => void;
}

export function RecommendationCard({ item, activeAction, onTrack }: RecommendationCardProps) {
  const actionKey = (eventType: EventType) => `${item.recommendation_id ?? item.vehicle_id}:${eventType}`;

  return (
    <article className="panel overflow-hidden">
      <div className="border-b border-slate-100 bg-gradient-to-r from-brand-50 via-white to-orange-50 px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="kicker">Rank #{item.rank}</div>
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
            <button
              type="button"
              className="button-primary gap-2"
              disabled={activeAction === actionKey("click")}
              onClick={() => onTrack("click", item)}
            >
              <MousePointerClick className="h-4 w-4" />
              {activeAction === actionKey("click") ? "Updating..." : "Track Click"}
            </button>
            <button
              type="button"
              className="button-secondary gap-2"
              disabled={activeAction === actionKey("save")}
              onClick={() => onTrack("save", item)}
            >
              <Heart className="h-4 w-4" />
              Save Match
            </button>
            <button
              type="button"
              className="button-secondary gap-2"
              disabled={activeAction === actionKey("test_drive_request")}
              onClick={() => onTrack("test_drive_request", item)}
            >
              <CarFront className="h-4 w-4" />
              Request Test Drive
            </button>
            <button
              type="button"
              className="button-secondary gap-2"
              disabled={activeAction === actionKey("reject")}
              onClick={() => onTrack("reject", item)}
            >
              <ThumbsDown className="h-4 w-4" />
              Reject
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

