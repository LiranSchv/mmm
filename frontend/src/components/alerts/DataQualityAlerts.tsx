import { AlertTriangle, Info, XCircle, CheckCircle } from "lucide-react";

interface Warning {
  level: "error" | "warning" | "info" | "success";
  code: string;
  message: string;
}

const icons = {
  error:   <XCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />,
  warning: <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />,
  info:    <Info className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" />,
  success: <CheckCircle className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />,
};

const bg = {
  error:   "bg-red-50 border-red-200",
  warning: "bg-amber-50 border-amber-200",
  info:    "bg-blue-50 border-blue-200",
  success: "bg-green-50 border-green-200",
};

const text = {
  error:   "text-red-800",
  warning: "text-amber-800",
  info:    "text-blue-800",
  success: "text-green-800",
};

export function DataQualityAlerts({ warnings }: { warnings: Warning[] }) {
  if (!warnings.length) return null;
  return (
    <div className="space-y-2">
      {warnings.map((w, i) => (
        <div
          key={i}
          className={`flex gap-3 rounded-lg border px-4 py-3 ${bg[w.level]}`}
        >
          {icons[w.level]}
          <p className={`text-sm ${text[w.level]}`}>{w.message}</p>
        </div>
      ))}
    </div>
  );
}
