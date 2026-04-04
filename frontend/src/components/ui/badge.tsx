import { cn } from "@/lib/utils";

type Variant = "error" | "warning" | "info" | "success" | "default";

const variants: Record<Variant, string> = {
  error:   "bg-red-50 text-red-700 border-red-200",
  warning: "bg-amber-50 text-amber-700 border-amber-200",
  info:    "bg-blue-50 text-blue-700 border-blue-200",
  success: "bg-green-50 text-green-700 border-green-200",
  default: "bg-gray-100 text-gray-700 border-gray-200",
};

export function Badge({
  variant = "default",
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: Variant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
