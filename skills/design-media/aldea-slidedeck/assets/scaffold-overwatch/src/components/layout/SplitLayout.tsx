import type { ReactNode } from "react";

interface SplitLayoutProps {
  left: ReactNode;
  right: ReactNode;
  className?: string;
  ratio?: "1:1" | "2:1" | "1:2" | "3:2" | "2:3";
  gap?: "sm" | "md" | "lg" | "xl";
}

export function SplitLayout({ left, right, className = "", ratio = "1:1", gap = "lg" }: SplitLayoutProps) {
  const ratios: Record<string, string> = {
    "1:1": "grid-cols-2",
    "2:1": "grid-cols-[2fr_1fr]",
    "1:2": "grid-cols-[1fr_2fr]",
    "3:2": "grid-cols-[3fr_2fr]",
    "2:3": "grid-cols-[2fr_3fr]",
  };
  const gaps: Record<string, string> = { sm: "gap-6", md: "gap-8", lg: "gap-12", xl: "gap-16" };
  return (
    <div className={`grid h-full ${ratios[ratio]} ${gaps[gap]} ${className}`}>
      <div className="flex flex-col justify-center">{left}</div>
      <div className="flex flex-col justify-center">{right}</div>
    </div>
  );
}
