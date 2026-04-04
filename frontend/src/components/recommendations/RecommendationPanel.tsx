"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { TrendingUp, TrendingDown, AlertTriangle, Info } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { fmt, fmtPct } from "@/lib/utils";

interface Shift {
  channel: string;
  current_pct: number;
  optimal_pct: number;
  delta_pct: number;
  delta_abs: number;
  direction: "increase" | "decrease";
}

interface Lift {
  current_ftbs: number;
  projected_ftbs: number;
  lift_pct: number;
  lift_abs: number;
  ci_low_pct: number;
  ci_high_pct: number;
}

interface Alert { channel: string; level: string; message: string }

interface Props {
  narrative: string;
  shifts: Shift[];
  expected_lift: Lift;
  saturation_alerts: Alert[];
}

export function RecommendationPanel({ narrative, shifts, expected_lift, saturation_alerts }: Props) {
  const chartData = shifts.map((s) => ({
    channel: s.channel,
    delta: s.delta_pct,
  }));

  return (
    <div className="space-y-6">
      {/* Expected lift banner */}
      <div className="rounded-xl bg-gradient-to-r from-indigo-50 to-emerald-50 border border-indigo-100 p-6">
        <p className="text-sm font-medium text-gray-600 mb-1">Expected FTB lift (30 days)</p>
        <div className="flex items-end gap-4">
          <span className="text-4xl font-bold text-indigo-700">
            +{fmt(expected_lift.lift_abs)}
          </span>
          <span className="text-xl font-semibold text-indigo-500 mb-1">
            ({fmtPct(expected_lift.lift_pct)})
          </span>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Confidence range: +{expected_lift.ci_low_pct}% to +{expected_lift.ci_high_pct}%
          · Based on {fmt(expected_lift.current_ftbs)} current FTBs
        </p>
      </div>

      {/* Written narrative */}
      <Card>
        <CardHeader><CardTitle>Recommended action</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-gray-700 leading-relaxed">{narrative}</p>
        </CardContent>
      </Card>

      {/* Budget shift chart */}
      <Card>
        <CardHeader><CardTitle>Recommended budget shifts</CardTitle></CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 70 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f0f0f0" />
              <XAxis type="number" unit="%" tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="channel" tick={{ fontSize: 11 }} width={70} />
              <Tooltip formatter={(v: number) => `${v > 0 ? "+" : ""}${v.toFixed(1)}%`} />
              <ReferenceLine x={0} stroke="#d1d5db" />
              <Bar dataKey="delta" name="Budget shift" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.delta >= 0 ? "#10b981" : "#ef4444"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {/* Shift table */}
          <div className="mt-4 divide-y divide-gray-50">
            {shifts.map((s) => (
              <div key={s.channel} className="flex items-center justify-between py-2.5">
                <div className="flex items-center gap-2">
                  {s.direction === "increase"
                    ? <TrendingUp className="h-4 w-4 text-emerald-500" />
                    : <TrendingDown className="h-4 w-4 text-red-400" />
                  }
                  <span className="text-sm font-medium text-gray-700">{s.channel}</span>
                </div>
                <div className="text-right">
                  <span className={`text-sm font-semibold ${s.direction === "increase" ? "text-emerald-600" : "text-red-500"}`}>
                    {fmtPct(s.delta_pct)}
                  </span>
                  <span className="text-xs text-gray-400 ml-2">
                    ({s.current_pct}% → {s.optimal_pct}%)
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Saturation alerts */}
      {saturation_alerts.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Channel alerts</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {saturation_alerts.map((a, i) => (
              <div
                key={i}
                className={`flex gap-3 rounded-lg px-4 py-3 border ${
                  a.level === "warning"
                    ? "bg-amber-50 border-amber-200"
                    : "bg-blue-50 border-blue-200"
                }`}
              >
                {a.level === "warning"
                  ? <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                  : <Info className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" />
                }
                <p className="text-sm text-gray-700">{a.message}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
