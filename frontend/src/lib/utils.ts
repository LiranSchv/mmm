import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function fmt(n: number, decimals = 0) {
  return n.toLocaleString("en-US", { maximumFractionDigits: decimals });
}

export function fmtPct(n: number) {
  return `${n > 0 ? "+" : ""}${n.toFixed(1)}%`;
}

export const MODEL_COLORS: Record<string, string> = {
  pymc: "#6366f1",
  robyn: "#f59e0b",
  meridian: "#10b981",
};

export const CHANNEL_COLORS = [
  "#6366f1", "#f59e0b", "#10b981", "#ef4444",
  "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6",
];
