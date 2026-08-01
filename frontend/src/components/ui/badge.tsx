import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const styles = {
  POTENTIAL_MATCH: "border-teal-200 bg-teal-50 text-teal-800",
  EXCLUDED: "border-rose-200 bg-rose-50 text-rose-800",
  MISSING_INFORMATION: "border-amber-200 bg-amber-50 text-amber-800",
  MANUAL_REVIEW: "border-blue-200 bg-blue-50 text-blue-800",
  MET: "border-teal-200 bg-teal-50 text-teal-800",
  NOT_MET: "border-rose-200 bg-rose-50 text-rose-800",
  UNKNOWN: "border-amber-200 bg-amber-50 text-amber-800",
  CONTRADICTORY: "border-blue-200 bg-blue-50 text-blue-800",
} as const;

export function Badge({
  status,
  className,
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { status?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-bold tracking-[0.06em]",
        status && styles[status as keyof typeof styles],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}

