"use client";

import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Label,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { CHANNEL_COLORS, MODEL_COLORS, fmt } from "@/lib/utils";

interface CurvePoint { spend: number; response: number }
interface ChannelSaturation {
  channel: string;
  curve_points: CurvePoint[];
  current_spend: number;
  threshold: number;
  is_saturated: boolean;
}
interface ModelResult {
  model_name: string;
  saturation: ChannelSaturation[] | null;
}

export function SaturationCurves({ models }: { models: ModelResult[] }) {
  const allChannels = Array.from(
    new Set(models.flatMap((m) => (m.saturation ?? []).map((s: ChannelSaturation) => s.channel)))
  );
  const [activeChannel, setActiveChannel] = useState(allChannels[0]);

  const channelData = models
    .map((m) => ({
      model: m.model_name,
      sat: (m.saturation ?? []).find((s) => s.channel === activeChannel),
    }))
    .filter((x) => x.sat);

  // Merge all curve points by spend for the chart
  const allPoints = channelData.flatMap((x) => x.sat!.curve_points.map((p) => p.spend));
  const uniqueSpends = Array.from(new Set(allPoints)).sort((a, b) => a - b);

  const chartData = uniqueSpends.map((spend) => {
    const row: Record<string, number> = { spend };
    for (const { model, sat } of channelData) {
      const pt = sat!.curve_points.find((p) => Math.abs(p.spend - spend) < 1);
      if (pt) row[model] = pt.response;
    }
    return row;
  });

  const currentSpend = channelData[0]?.sat?.current_spend ?? 0;
  const threshold = channelData[0]?.sat?.threshold ?? 0;
  const isSaturated = channelData[0]?.sat?.is_saturated ?? false;

  return (
    <div className="space-y-6">
      {/* Channel selector */}
      <div className="flex flex-wrap gap-2">
        {allChannels.map((ch, i) => (
          <button
            key={ch}
            onClick={() => setActiveChannel(ch)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium border transition-colors ${
              activeChannel === ch
                ? "text-white border-transparent"
                : "border-gray-200 text-gray-600 hover:border-gray-300"
            }`}
            style={activeChannel === ch ? { background: CHANNEL_COLORS[i % CHANNEL_COLORS.length] } : {}}
          >
            {ch}
          </button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Saturation curve — {activeChannel}</CardTitle>
            {isSaturated && (
              <span className="text-xs font-medium text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-3 py-1">
                ⚠ Saturated
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Current avg. daily spend: <strong>${fmt(currentSpend)}</strong> ·
            Diminishing returns threshold: <strong>${fmt(threshold)}</strong>
          </p>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={340}>
            <LineChart data={chartData} margin={{ left: 16, right: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="spend"
                tickFormatter={(v) => `$${fmt(v)}`}
                tick={{ fontSize: 11 }}
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(v: number, name: string) => [v.toFixed(3), name.toUpperCase()]}
                labelFormatter={(v) => `Spend: $${fmt(Number(v))}`}
              />
              {models.map((m) => (
                <Line
                  key={m.model_name}
                  type="monotone"
                  dataKey={m.model_name}
                  name={m.model_name}
                  stroke={MODEL_COLORS[m.model_name] ?? "#888"}
                  dot={false}
                  strokeWidth={2}
                />
              ))}
              <ReferenceLine x={currentSpend} stroke="#6366f1" strokeDasharray="4 4">
                <Label value="Current" position="top" fontSize={11} fill="#6366f1" />
              </ReferenceLine>
              <ReferenceLine x={threshold} stroke="#f59e0b" strokeDasharray="4 4">
                <Label value="Threshold" position="top" fontSize={11} fill="#f59e0b" />
              </ReferenceLine>
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
