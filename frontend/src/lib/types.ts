export interface ValidationWarning {
  level: "error" | "warning" | "info" | "success";
  code: string;
  message: string;
}

export interface Dataset {
  id: string;
  filename: string;
  row_count: number;
  columns: string[];
  date_range: { min: string; max: string } | null;
  dimensions: Record<string, string[]>;
  validation_warnings: ValidationWarning[];
  grain_config: GrainConfig | null;
}

export interface GrainConfig {
  time: "daily" | "weekly";
  dimensions: string[];
}

export interface Job {
  id: string;
  dataset_id: string;
  status: "pending" | "running" | "completed" | "failed";
  models_requested: string[];
  created_at: string;
  completed_at: string | null;
  model_statuses: { model: string; status: string; error: string | null }[];
  error: string | null;
}

export interface Contribution {
  channel: string;
  contribution_pct: number;
  spend: number;
  roi?: number;
}

export interface SaturationPoint { spend: number; response: number }

export interface ChannelSaturation {
  channel: string;
  curve_points: SaturationPoint[];
  current_spend: number;
  threshold: number;
  is_saturated: boolean;
}

export interface ModelResult {
  model_name: string;
  status: string;
  metrics: { r2: number; mape: number; nrmse: number } | null;
  contributions: Contribution[] | null;
  saturation: ChannelSaturation[] | null;
  decomposition: Record<string, number>[] | null;
  error?: string | null;
}

export interface Comparison {
  models: string[];
  metrics_table: { model: string; r2: number; mape: number; nrmse: number }[];
  contribution_chart: Record<string, number | string>[];
  agreement_score: number | null;
}

export interface ResultsResponse {
  job_id: string;
  job_status: string;
  models: ModelResult[];
  comparison: Comparison;
}

export interface Shift {
  channel: string;
  current_pct: number;
  optimal_pct: number;
  delta_pct: number;
  delta_abs: number;
  direction: "increase" | "decrease";
}

export interface Lift {
  current_ftbs: number;
  projected_ftbs: number;
  lift_pct: number;
  lift_abs: number;
  ci_low_pct: number;
  ci_high_pct: number;
}

export interface RecommendationsResponse {
  narrative: string;
  shifts: Shift[];
  expected_lift: Lift;
  saturation_alerts: { channel: string; level: string; message: string }[];
  total_budget: number;
  horizon_days: number;
}
