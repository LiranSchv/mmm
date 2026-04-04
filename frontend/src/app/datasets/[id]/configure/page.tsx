"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getDataset, updateGrain, createJob, getSupportedCountries } from "@/lib/api";
import type { GrainConfig } from "@/lib/types";
import { GrainSelector } from "@/components/grain-selector/GrainSelector";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { MODEL_COLORS } from "@/lib/utils";

const MODELS = [
  { id: "pymc",    label: "PyMC-Marketing", desc: "Bayesian MMM with full posterior uncertainty" },
  { id: "robyn",   label: "Robyn",          desc: "Meta's open-source MMM with Pareto optimisation" },
  { id: "meridian",label: "Meridian",       desc: "Google's Bayesian hierarchical MMM" },
];

export default function ConfigurePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const { data: ds } = useQuery({ queryKey: ["dataset", id], queryFn: () => getDataset(id) });
  const { data: countries } = useQuery({ queryKey: ["countries"], queryFn: getSupportedCountries });

  const [grain, setGrain] = useState<GrainConfig | null>(null);
  const [selectedModels, setSelectedModels] = useState<string[]>(["pymc", "robyn", "meridian"]);
  const [selectedCountries, setSelectedCountries] = useState<string[]>([]);
  const [dow, setDow] = useState(true);
  const [launching, setLaunching] = useState(false);

  const toggleModel = (m: string) =>
    setSelectedModels((prev) => prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]);

  const toggleCountry = (c: string) =>
    setSelectedCountries((prev) => prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]);

  async function handleLaunch() {
    if (!grain || selectedModels.length === 0) return;
    setLaunching(true);
    try {
      await updateGrain(id, grain);
      const job: any = await createJob({
        dataset_id: id,
        models: selectedModels,
        grain,
        seasonality: { dow, countries: selectedCountries },
      });
      router.push(`/jobs/${job.id}`);
    } catch (e: any) {
      alert(e.message);
      setLaunching(false);
    }
  }

  const dims = ds ? Object.keys(ds.dimensions ?? {}) : [] as string[];

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configure model run</h1>
        <p className="text-sm text-gray-500 mt-1">{ds?.filename}</p>
      </div>

      {/* Grain */}
      <GrainSelector
        availableDimensions={dims}
        initial={ds?.grain_config ?? undefined}
        onSave={(g) => setGrain(g)}
      />

      {/* Model selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select models to run</CardTitle>
          <p className="text-sm text-gray-500 mt-0.5">Run one, two, or all three for comparison.</p>
        </CardHeader>
        <CardContent className="space-y-3">
          {MODELS.map((m) => (
            <label
              key={m.id}
              className={`flex items-center gap-4 rounded-lg border p-4 cursor-pointer transition-colors ${
                selectedModels.includes(m.id)
                  ? "border-brand bg-brand/5"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <input
                type="checkbox"
                checked={selectedModels.includes(m.id)}
                onChange={() => toggleModel(m.id)}
                className="accent-brand h-4 w-4"
              />
              <span
                className="h-3 w-3 rounded-full"
                style={{ background: MODEL_COLORS[m.id] }}
              />
              <div>
                <p className="text-sm font-semibold text-gray-800">{m.label}</p>
                <p className="text-xs text-gray-500">{m.desc}</p>
              </div>
            </label>
          ))}
        </CardContent>
      </Card>

      {/* Seasonality */}
      <Card>
        <CardHeader>
          <CardTitle>Seasonality</CardTitle>
          <p className="text-sm text-gray-500 mt-0.5">
            Seasonality features are passed to each model's native API.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Day of week */}
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={dow}
              onChange={(e) => setDow(e.target.checked)}
              className="accent-brand h-4 w-4"
            />
            <div>
              <p className="text-sm font-medium text-gray-700">In-week seasonality (day-of-week)</p>
              <p className="text-xs text-gray-500">Captures weekend/weekday patterns</p>
            </div>
          </label>

          {/* Countries */}
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">National holidays</p>
            <div className="flex flex-wrap gap-2">
              {(countries ?? []).map((c: { code: string; name: string }) => (
                <button
                  key={c.code}
                  onClick={() => toggleCountry(c.code)}
                  className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                    selectedCountries.includes(c.code)
                      ? "border-brand bg-brand/10 text-brand"
                      : "border-gray-200 text-gray-600 hover:border-gray-300"
                  }`}
                >
                  {c.code} — {c.name}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Launch */}
      <div className="flex justify-end">
        <Button
          size="lg"
          onClick={handleLaunch}
          disabled={!grain || selectedModels.length === 0 || launching}
        >
          {launching ? <><Spinner className="h-4 w-4" /> Launching…</> : "Run models →"}
        </Button>
      </div>
    </div>
  );
}
