"use client";

import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { getJob } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { MODEL_COLORS } from "@/lib/utils";
import { CheckCircle, XCircle, Clock } from "lucide-react";
import { useEffect } from "react";

const STATUS_ICON: Record<string, React.ReactNode> = {
  completed: <CheckCircle className="h-5 w-5 text-emerald-500" />,
  failed:    <XCircle className="h-5 w-5 text-red-500" />,
  running:   <Spinner className="h-5 w-5" />,
  pending:   <Clock className="h-5 w-5 text-gray-400" />,
};

export default function JobPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const { data: job, refetch } = useQuery({
    queryKey: ["job", id],
    queryFn: () => getJob(id),
    refetchInterval: (q) =>
      q.state.data?.status === "completed" || q.state.data?.status === "failed"
        ? false
        : 5000,
  });

  useEffect(() => {
    if (job?.status === "completed") {
      router.push(`/results/${id}`);
    }
  }, [job?.status, id, router]);

  const allDone = job?.status === "completed" || job?.status === "failed";

  return (
    <div className="max-w-lg mx-auto space-y-6 pt-8">
      <div className="text-center space-y-2">
        {!allDone && <Spinner className="mx-auto h-10 w-10" />}
        <h1 className="text-2xl font-bold text-gray-900">
          {job?.status === "failed" ? "Run failed" : job?.status === "completed" ? "Complete!" : "Running models…"}
        </h1>
        <p className="text-sm text-gray-500">
          {!allDone && "This can take a few minutes. You'll be redirected automatically."}
          {job?.status === "failed" && "One or more models encountered an error."}
        </p>
      </div>

      <Card>
        <CardContent className="py-4 divide-y divide-gray-50">
          {(job?.model_statuses ?? []).map((m: any) => (
            <div key={m.model} className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ background: MODEL_COLORS[m.model] ?? "#888" }}
                />
                <span className="text-sm font-medium text-gray-700 capitalize">{m.model}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400 capitalize">{m.status}</span>
                {STATUS_ICON[m.status] ?? null}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {job?.status === "failed" && (
        <div className="flex justify-center gap-3">
          <Button variant="secondary" onClick={() => router.back()}>Go back</Button>
          <Button onClick={() => refetch()}>Refresh</Button>
        </div>
      )}
    </div>
  );
}
