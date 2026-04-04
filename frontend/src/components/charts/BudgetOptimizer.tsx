"use client";

import { useState, useEffect, useCallback } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { simulateBudget } from "@/lib/api";
import { fmt, fmtPct, CHANNEL_COLORS } from "@/lib/utils";

interface Contribution { channel: string; contribution_pct: number; spend: number }

interface Props {
  jobId: string;
  contributions: Contribution[];   // ensemble contributions
  totalBudget: number;
}

export function BudgetOptimizer({ jobId, contributions, totalBudget }: Props) {
  const channels = contributions.map((c) => c.channel);

  // Allocation state: {channel: pct}
  const [alloc, setAlloc] = useState<Record<string, number>>(() =>
    Object.fromEntries(contributions.map((c) => [c.channel, c.contribution_pct]))
  );
  const [simulation, setSimulation] = useState<{ projected_ftbs: number; channel_projections: any[] } | null>(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = useCallback(async () => {
    setLoading(true);
    try {
      const result = await simulateBudget(jobId, alloc, totalBudget);
      setSimulation(result);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [jobId, alloc, totalBudget]);

  useEffect(() => {
    const timer = setTimeout(runSimulation, 500);
    return () => clearTimeout(timer);
  }, [runSimulation]);

  const totalAlloc = Object.values(alloc).reduce((a, b) => a + b, 0);

  const updateChannel = (ch: string, pct: number) => {
    setAlloc((prev) => ({ ...prev, [ch]: pct }));
  };

  // Chart data: current vs optimized
  const chartData = channels.map((ch) => ({
    channel: ch,
    current: contributions.find((c) => c.channel === ch)?.contribution_pct ?? 0,
    optimized: alloc[ch] ?? 0,
  }));

  return (
    <div className="space-y-6">
      {/* Projected FTB banner */}
      {simulation && (
        <div className="rounded-xl bg-indigo-50 border border-indigo-100 px-6 py-4 flex items-center justify-between">
          <div>
            <p className="text-sm text-indigo-700 font-medium">Projected FTBs (30 days)</p>
            <p className="text-3xl font-bold text-indigo-800 mt-0.5">
              {fmt(simulation.projected_ftbs)}
            </p>
          </div>
          {loading && <div className="text-xs text-indigo-400">Recalculating…</div>}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sliders */}
        <Card>
          <CardHeader>
            <CardTitle>Budget allocation</CardTitle>
            <p className="text-xs text-gray-400 mt-1">
              Total: {totalAlloc.toFixed(1)}% of ${fmt(totalBudget)}
              {Math.abs(totalAlloc - 100) > 1 && (
                <span className="text-amber-500 ml-2">— allocate exactly 100%</span>
              )}
            </p>
          </CardHeader>
          <CardContent className="space-y-5">
            {channels.map((ch, i) => (
              <div key={ch}>
                <div className="flex justify-between text-sm mb-1.5">
                  <span className="font-medium text-gray-700 flex items-center gap-2">
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ background: CHANNEL_COLORS[i % CHANNEL_COLORS.length] }}
                    />
                    {ch}
                  </span>
                  <span className="font-mono text-gray-600">
                    {alloc[ch]?.toFixed(1)}% · ${fmt((alloc[ch] / 100) * totalBudget)}
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={60}
                  step={0.5}
                  value={alloc[ch] ?? 0}
                  onChange={(e) => updateChannel(ch, Number(e.target.value))}
                  className="w-full accent-brand"
                />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Before/after chart */}
        <Card>
          <CardHeader><CardTitle>Current vs. optimized (%)</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={chartData} layout="vertical" margin={{ left: 60 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
                <XAxis type="number" unit="%" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="channel" tick={{ fontSize: 11 }} width={60} />
                <Tooltip formatter={(v: number) => `${v.toFixed(1)}%`} />
                <Legend />
                <Bar dataKey="current" name="Current" fill="#e5e7eb" radius={[0, 4, 4, 0]} />
                <Bar dataKey="optimized" name="Optimized" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
