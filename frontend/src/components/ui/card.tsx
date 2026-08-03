import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-2xl border border-[#d9e3e9] bg-white/95 shadow-[0_2px_8px_rgba(16,35,59,0.045)]", className)}
      {...props}
    />
  );
}
