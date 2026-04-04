"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { MODEL_COLORS, CHANNEL_COLORS, fmt } from "@/lib/utils";

interface Props {
  comparison: {
    models: string[];
    metrics_table: Array<{ model: string; r2: number; mape: number; nrmse: number }>;
    contribution_chart: Array<Record<string, number | string>>;
    agreement_score: number | null;
  };
}

export function ModelComparison({ comparison }: Props) {
  const { models, metrics_table, contribution_chart, agreement_score } = comparison;

  return (
    <div className="space-y-6">
      {/* Agreement score */}
      {agreement_score != null && (
        <div className="rounded-lg bg-indigo-50 border border-indigo-100 px-4 py-3 flex items-center gap-3">
          <div className="text-2xl font-bold text-indigo-600">
            {(agreement_score * 100).toFixed(0)}%
          </div>
          <div>
            <p className="text-sm font-medium text-indigo-800">Model agreement score</p>
            <p className="text-xs text-indigo-600">
              How consistently models rank channels by contribution
            </p>
          </div>
        </div>
      )}

      {/* Metrics table */}
      <Card>
        <CardHeader><CardTitle>Model fit metrics</CardTitle></CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {["Model", "R²", "MAPE (%)", "NRMSE"].map((h) => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {metrics_table.map((row) => (
                <tr key={row.model} className="hover:bg-gray-50">
                  <td className="px-6 py-3">
                    <span
                      className="inline-flex items-center gap-2 font-medium capitalize"
                    >
                      <span
                        className="h-2.5 w-2.5 rounded-full"
                        style={{ background: MODEL_COLORS[row.model] ?? "#888" }}
                      />
                      {row.model}
                    </span>
                  </td>
                  <td className="px-6 py-3 font-mono">{row.r2?.toFixed(3) ?? "—"}</td>
                  <td className="px-6 py-3 font-mono">{row.mape?.toFixed(1) ?? "—"}</td>
                  <td className="px-6 py-3 font-mono">{row.nrmse?.toFixed(3) ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Channel contribution chart */}
      <Card>
        <CardHeader><CardTitle>Channel contribution by model (%)</CardTitle></CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={contribution_chart} margin={{ left: 0, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="channel" tick={{ fontSize: 12 }} />
              <YAxis unit="%" tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: number) => `${v?.toFixed(1)}%`} />
              <Legend />
              {models.map((m, i) => (
                <Bar key={m} dataKey={m} name={m.toUpperCase()} fill={MODEL_COLORS[m] ?? CHANNEL_COLORS[i]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
