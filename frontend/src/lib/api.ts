import type {
  Dataset, Job, ResultsResponse, RecommendationsResponse, GrainConfig,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

// ── Datasets ──────────────────────────────────────────────────────────────────
export async function uploadDataset(file: File): Promise<Dataset & { summary: unknown }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/datasets/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error((await res.json()).detail ?? "Upload failed");
  return res.json();
}

export const getDataset = (id: string) => request<Dataset>(`/datasets/${id}`);

export const previewDataset = (id: string, rows = 50) =>
  request<{ columns: string[]; rows: Record<string, unknown>[]; total_rows: number }>(
    `/datasets/${id}/preview?rows=${rows}`
  );

export const updateGrain = (id: string, grain: GrainConfig) =>
  request<Dataset>(`/datasets/${id}/grain`, {
    method: "PATCH",
    body: JSON.stringify(grain),
  });

// ── Jobs ──────────────────────────────────────────────────────────────────────
export async function createJob(payload: {
  dataset_id: string;
  models: string[];
  grain?: GrainConfig;
  seasonality?: object;
  horizon_days?: number;
}): Promise<Job> {
  return request<Job>("/jobs/", { method: "POST", body: JSON.stringify(payload) });
}

export const getJob = (id: string) => request<Job>(`/jobs/${id}`);

// ── Results ───────────────────────────────────────────────────────────────────
export const getResults = (jobId: string) => request<ResultsResponse>(`/results/${jobId}`);

// ── Recommendations ───────────────────────────────────────────────────────────
export const getRecommendations = (jobId: string, totalBudget: number, horizonDays = 30) =>
  request<RecommendationsResponse>(
    `/recommendations/${jobId}?total_budget=${totalBudget}&horizon_days=${horizonDays}`
  );

export async function simulateBudget(
  jobId: string,
  allocation: Record<string, number>,
  totalBudget: number,
  horizonDays = 30
) {
  return request<{ projected_ftbs: number; channel_projections: unknown[] }>(
    `/recommendations/${jobId}/simulate`,
    {
      method: "POST",
      body: JSON.stringify({
        allocation,
        total_budget: totalBudget,
        horizon_days: horizonDays,
      }),
    }
  );
}

export const getSupportedCountries = () =>
  request<{ code: string; name: string }[]>("/recommendations/meta/countries");
