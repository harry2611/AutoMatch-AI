export type BodyType = "suv" | "sedan" | "truck" | "ev" | "coupe" | "wagon";
export type FinancingPreference = "loan" | "lease" | "cash";
export type UrgencyLevel = "low" | "medium" | "high";
export type ExperimentArm = "heuristic" | "bayesian";
export type EventType =
  | "impression"
  | "click"
  | "save"
  | "reject"
  | "test_drive_request"
  | "dealer_response"
  | "search"
  | "conversion";

export interface RecommendationItem {
  recommendation_id: number | null;
  vehicle_id: number;
  dealer_id: number;
  rank: number;
  experiment_arm: ExperimentArm;
  ranking_strategy: string;
  brand: string;
  model: string;
  year: number;
  body_type: BodyType;
  condition: string;
  price: number;
  mileage: number;
  dealer_name: string;
  dealer_city: string;
  dealer_state: string;
  distance_miles: number;
  purchase_probability: number;
  ranking_score: number;
  expected_revenue: number;
  dealer_quality: number;
  inventory_score: number;
  inventory_status: string;
  explanation: string[];
  explanation_text: string;
  features: string[];
  photo_url?: string | null;
}

export interface RecommendationResponse {
  buyer_id: number;
  recommendation_version: string;
  experiment_name?: string | null;
  experiment_arm: ExperimentArm;
  ranking_strategy: string;
  recommendations: RecommendationItem[];
}

export interface EventResponse {
  event_id: number;
  message: string;
  posterior_snapshot: Record<string, number>;
  reranked_recommendations?: RecommendationResponse | null;
}

export interface DealerListItem {
  id: number;
  name: string;
  city: string;
  state: string;
  zip_code: string;
  average_response_minutes: number;
  quality_score: number;
  response_rate: number;
}

export interface LeadItem {
  buyer_id: number;
  buyer_name: string;
  budget_max: number;
  urgency: UrgencyLevel;
  vehicle_label: string;
  purchase_probability: number;
  created_at: string;
}

export interface VehicleDemandItem {
  vehicle_id: number;
  label: string;
  clicks: number;
  saves: number;
  test_drive_requests: number;
}

export interface TrendPoint {
  date: string;
  recommendation_count: number;
  conversion_count: number;
  close_rate: number;
}

export interface PricingGapItem {
  vehicle_id: number;
  label: string;
  current_price: number;
  market_median_price: number;
  gap_amount: number;
}

export interface ResponseTimeImpactItem {
  bucket: string;
  conversion_rate: number;
  recommendation_count: number;
}

export interface DealerDashboardResponse {
  dealer: DealerListItem;
  high_intent_leads: LeadItem[];
  vehicle_demand: VehicleDemandItem[];
  close_rate_trend: TrendPoint[];
  pricing_gaps: PricingGapItem[];
  response_time_impact: ResponseTimeImpactItem[];
}

export interface MetricCard {
  name: string;
  value: number;
  label: string;
}

export interface ArmMetricSummary {
  arm: ExperimentArm;
  ctr: number;
  precision_at_k: number;
  conversion_rate: number;
  total_revenue: number;
  average_distance: number;
  dealer_response_rate: number;
}

export interface DailySeriesPoint {
  date: string;
  heuristic_ctr: number;
  bayesian_ctr: number;
  heuristic_conversion_rate: number;
  bayesian_conversion_rate: number;
}

export interface AnalyticsOverviewResponse {
  headline_metrics: MetricCard[];
  arms: ArmMetricSummary[];
  conversion_lift: number;
  revenue_lift: number;
  average_match_distance: number;
  daily_series: DailySeriesPoint[];
}

export interface ExperimentResponse {
  id: number;
  name: string;
  description: string;
  status: string;
  traffic_split: number;
  control_arm: ExperimentArm;
  treatment_arm: ExperimentArm;
  created_at: string;
}

export interface ExperimentDashboardResponse {
  experiments: ExperimentResponse[];
  active_experiment?: ExperimentResponse | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    email: string;
    full_name: string;
    role: string;
    dealer_id?: number | null;
  };
}

