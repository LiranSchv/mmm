"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const TIME_OPTIONS = ["daily", "weekly"] as const;
const DIMENSION_OPTIONS = ["channel", "geo", "game", "platform"] as const;

interface Props {
  availableDimensions: string[];
  initial?: { time: string; dimensions: string[] };
  onSave: (grain: { time: "daily" | "weekly"; dimensions: string[] }) => void;
}

export function GrainSelector({ availableDimensions, initial, onSave }: Props) {
  const [time, setTime] = useState<"daily" | "weekly">((initial?.time as "daily" | "weekly") ?? "weekly");
  const [dims, setDims] = useState<string[]>(
    initial?.dimensions ?? ["channel", "geo"]
  );

  const toggleDim = (d: string) =>
    setDims((prev) => prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Modeling Grain</CardTitle>
        <p className="text-sm text-gray-500 mt-0.5">
          Choose how to aggregate your raw data before running models.
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Time grain */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Time granularity</p>
          <div className="flex gap-2">
            {TIME_OPTIONS.map((t) => (
              <button
                key={t}
                onClick={() => setTime(t as "daily" | "weekly")}
                className={`rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                  time === t
                    ? "border-brand bg-brand/10 text-brand"
                    : "border-gray-200 text-gray-600 hover:border-gray-300"
                }`}
              >
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Dimension selection */}
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">
            Dimensions to model by
          </p>
          <div className="flex flex-wrap gap-2">
            {DIMENSION_OPTIONS.filter((d) => availableDimensions.includes(d)).map((d) => (
              <button
                key={d}
                onClick={() => toggleDim(d)}
                className={`rounded-lg border px-4 py-2 text-sm font-medium capitalize transition-colors ${
                  dims.includes(d)
                    ? "border-brand bg-brand/10 text-brand"
                    : "border-gray-200 text-gray-600 hover:border-gray-300"
                }`}
              >
                {d}
              </button>
            ))}
          </div>
          {dims.length === 0 && (
            <p className="text-xs text-amber-600 mt-2">
              Select at least one dimension.
            </p>
          )}
          <p className="text-xs text-gray-400 mt-2">
            Grain: <strong>{time}</strong> ×{" "}
            <strong>{dims.length ? dims.join(" × ") : "total"}</strong>
          </p>
        </div>

        <Button onClick={() => onSave({ time, dimensions: dims })} disabled={dims.length === 0}>
          Save grain
        </Button>
      </CardContent>
    </Card>
  );
}
