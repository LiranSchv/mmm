"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { DropZone } from "@/components/upload/DropZone";
import { DataQualityAlerts } from "@/components/alerts/DataQualityAlerts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { uploadDataset } from "@/lib/api";
import { BarChart2, Layers, Zap } from "lucide-react";

const FEATURES = [
  { icon: <Layers className="h-5 w-5 text-brand" />, title: "Three MMM engines", desc: "Robyn, Meridian & PyMC-Marketing in one run" },
  { icon: <BarChart2 className="h-5 w-5 text-brand" />, title: "Compare & validate", desc: "Side-by-side metrics, saturation curves, channel attribution" },
  { icon: <Zap className="h-5 w-5 text-brand" />, title: "Actionable recs", desc: "Budget shift recommendations with expected FTB lift" },
];

export default function HomePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [warnings, setWarnings] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(file: File) {
    setLoading(true);
    setError(null);
    try {
      const data = await uploadDataset(file);
      setWarnings(data.validation_warnings ?? []);
      // Small delay so user sees alerts, then navigate
      setTimeout(() => router.push(`/datasets/${data.id}`), warnings.length ? 1500 : 300);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="text-center space-y-2 pt-4">
        <h1 className="text-3xl font-bold text-gray-900">Marketing Mix Modeling</h1>
        <p className="text-gray-500">
          Upload your spend + FTB data and compare Robyn, Meridian, and PyMC-Marketing
          to get channel attribution and budget recommendations.
        </p>
      </div>

      {/* Feature pills */}
      <div className="grid grid-cols-3 gap-4">
        {FEATURES.map((f) => (
          <div key={f.title} className="rounded-xl border border-gray-200 bg-white p-4 text-center space-y-2">
            <div className="flex justify-center">{f.icon}</div>
            <p className="text-sm font-semibold text-gray-800">{f.title}</p>
            <p className="text-xs text-gray-500">{f.desc}</p>
          </div>
        ))}
      </div>

      <Card>
        <CardHeader><CardTitle>Upload your data</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-gray-500">
            Required columns: <code className="bg-gray-100 px-1 rounded">date</code>,{" "}
            <code className="bg-gray-100 px-1 rounded">channel</code>,{" "}
            <code className="bg-gray-100 px-1 rounded">actual_spend</code>,{" "}
            <code className="bg-gray-100 px-1 rounded">ftbs</code>.
            Optional: <code className="bg-gray-100 px-1 rounded">geo</code>,{" "}
            <code className="bg-gray-100 px-1 rounded">game</code>,{" "}
            <code className="bg-gray-100 px-1 rounded">platform</code>.
          </p>
          <DropZone onUpload={handleUpload} loading={loading} />
          {error && <p className="text-sm text-red-600">{error}</p>}
          {warnings.length > 0 && <DataQualityAlerts warnings={warnings} />}
        </CardContent>
      </Card>
    </div>
  );
}
