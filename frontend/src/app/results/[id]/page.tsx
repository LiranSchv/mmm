"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getResults, getRecommendations } from "@/lib/api";
import { ModelComparison } from "@/components/charts/ModelComparison";
import { SaturationCurves } from "@/components/charts/SaturationCurves";
import { BudgetOptimizer } from "@/components/charts/BudgetOptimizer";
import { RecommendationPanel } from "@/components/recommendations/RecommendationPanel";
import { DataQualityAlerts } from "@/components/alerts/DataQualityAlerts";
import { Spinner } from "@/components/ui/spinner";

const TABS = [
  { id: "comparison",   label: "Model comparison" },
  { id: "saturation",   label: "Saturation curves" },
  { id: "optimizer",    label: "Budget optimizer" },
  { id: "recommendations", label: "Recommendations" },
];

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [tab, setTab] = useState("comparison");

  const { data: results, isLoading } = useQuery({
    queryKey: ["results", id],
    queryFn: () => getResults(id),
  });

  // Infer total budget from contributions
  const totalBudget = results
    ? (results.models ?? [])
        .filter((m: any) => m.status === "completed")
        .flatMap((m: any) => m.contributions ?? [])
        .reduce((sum: number, c: any) => sum + (c.spend ?? 0), 0) /
      Math.max((results.models ?? []).filter((m: any) => m.status === "completed").length, 1)
    : 0;

  const { data: recs } = useQuery({
    queryKey: ["recommendations", id, totalBudget],
    queryFn: () => getRecommendations(id, totalBudget),
    enabled: !!results && totalBudget > 0,
  });

  if (isLoading) {
    return <div className="flex justify-center py-20"><Spinner className="h-8 w-8" /></div>;
  }

  const completedModels = (results?.models ?? []).filter((m: any) => m.status === "completed");
  const failedModels = (results?.models ?? []).filter((m: any) => m.status === "failed");

  // Ensemble contributions: average across models
  const allChannels = Array.from(
    new Set(completedModels.flatMap((m: any) => (m.contributions ?? []).map((c: any) => c.channel)))
  ) as string[];

  const ensembleContribs = allChannels.map((ch) => {
    const entries = completedModels
      .flatMap((m: any) => m.contributions ?? [])
      .filter((c: any) => c.channel === ch);
    return {
      channel: ch,
      contribution_pct: entries.reduce((s: number, c: any) => s + c.contribution_pct, 0) / Math.max(entries.length, 1),
      spend: entries.reduce((s: number, c: any) => s + (c.spend ?? 0), 0) / Math.max(entries.length, 1),
    };
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Results</h1>
        <p className="text-sm text-gray-500 mt-1">
          {completedModels.length} model{completedModels.length !== 1 ? "s" : ""} completed
          {failedModels.length > 0 && ` · ${failedModels.length} failed`}
        </p>
      </div>

      {/* Failed model alerts */}
      {failedModels.length > 0 && (
        <DataQualityAlerts
          warnings={failedModels.map((m: any) => ({
            level: "warning" as const,
            code: "model_failed",
            message: `${m.model_name} failed to complete. ${m.error ?? ""}`,
          }))}
        />
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                tab === t.id
                  ? "border-brand text-brand"
                  : "border-transparent text-gray-500 hover:text-gray-800"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      <div className="min-h-96">
        {tab === "comparison" && results?.comparison && (
          <ModelComparison comparison={results.comparison} />
        )}

        {tab === "saturation" && (
          <SaturationCurves models={completedModels} />
        )}

        {tab === "optimizer" && (
          <BudgetOptimizer
            jobId={id}
            contributions={ensembleContribs}
            totalBudget={totalBudget}
          />
        )}

        {tab === "recommendations" && recs && (
          <RecommendationPanel
            narrative={recs.narrative}
            shifts={recs.shifts}
            expected_lift={recs.expected_lift}
            saturation_alerts={recs.saturation_alerts}
          />
        )}

        {tab === "recommendations" && !recs && (
          <div className="flex justify-center py-12">
            <Spinner />
          </div>
        )}
      </div>
    </div>
  );
}
