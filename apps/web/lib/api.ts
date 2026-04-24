import type { AnalyticsOverviewResponse, DealerDashboardResponse, EventResponse, ExperimentDashboardResponse, LoginResponse, RecommendationResponse } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

type RequestOptions = RequestInit & {
  token?: string;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function fetchRecommendations(payload: Record<string, unknown>): Promise<RecommendationResponse> {
  return request<RecommendationResponse>("/recommendations/query", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function trackEvent(payload: Record<string, unknown>): Promise<EventResponse> {
  return request<EventResponse>("/events", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchDealerDashboard(token: string): Promise<DealerDashboardResponse> {
  return request<DealerDashboardResponse>("/dealers/me/dashboard", { token });
}

export function fetchAnalytics(token: string): Promise<AnalyticsOverviewResponse> {
  return request<AnalyticsOverviewResponse>("/analytics/overview", { token });
}

export function fetchExperimentDashboard(token: string): Promise<ExperimentDashboardResponse> {
  return request<ExperimentDashboardResponse>("/experiments/dashboard", { token });
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatCompact(value: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

