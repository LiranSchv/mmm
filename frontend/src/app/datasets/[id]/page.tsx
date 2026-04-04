"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getDataset, previewDataset } from "@/lib/api";
import { DataQualityAlerts } from "@/components/alerts/DataQualityAlerts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { fmt } from "@/lib/utils";
import { ArrowRight, Calendar, Rows } from "lucide-react";

export default function DatasetPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const { data: ds, isLoading: dsLoading } = useQuery({
    queryKey: ["dataset", id],
    queryFn: () => getDataset(id),
  });

  const { data: preview } = useQuery({
    queryKey: ["dataset-preview", id],
    queryFn: () => previewDataset(id, 8),
    enabled: !!ds,
  });

  if (dsLoading) {
    return <div className="flex justify-center py-20"><Spinner className="h-8 w-8" /></div>;
  }

  const warnings = ds?.validation_warnings ?? [];
  const hasErrors = warnings.some((w: any) => w.level === "error");

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{ds?.filename}</h1>
          <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
            <span className="flex items-center gap-1">
              <Rows className="h-3.5 w-3.5" /> {fmt(ds?.row_count ?? 0)} rows
            </span>
            {ds?.date_range && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                {ds.date_range.min} → {ds.date_range.max}
              </span>
            )}
          </div>
        </div>
        <Button
          onClick={() => router.push(`/datasets/${id}/configure`)}
          disabled={hasErrors}
        >
          Configure model run <ArrowRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Validation alerts */}
      {warnings.length > 0 && <DataQualityAlerts warnings={warnings} />}

      {/* Dimensions summary */}
      {ds?.dimensions && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {Object.entries(ds.dimensions as Record<string, string[]>).map(([dim, vals]) => (
            <Card key={dim}>
              <CardContent className="py-4">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">{dim}</p>
                <div className="flex flex-wrap gap-1">
                  {vals.slice(0, 6).map((v) => (
                    <span key={v} className="text-xs bg-gray-100 text-gray-700 rounded px-2 py-0.5">{v}</span>
                  ))}
                  {vals.length > 6 && (
                    <span className="text-xs text-gray-400">+{vals.length - 6} more</span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Preview table */}
      {preview && (
        <Card>
          <CardHeader>
            <CardTitle>Data preview</CardTitle>
            <p className="text-xs text-gray-400 mt-0.5">First 8 rows of {fmt(preview.total_rows)} total</p>
          </CardHeader>
          <CardContent className="p-0 overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {preview.columns.map((col: string) => (
                    <th key={col} className="px-4 py-2.5 text-left font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {preview.rows.map((row: any, i: number) => (
                  <tr key={i} className="hover:bg-gray-50">
                    {preview.columns.map((col: string) => (
                      <td key={col} className="px-4 py-2 text-gray-700 whitespace-nowrap font-mono">
                        {row[col]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
