import type { ReactNode } from "react";

interface GridLayoutProps {
  children: ReactNode;
  columns?: 2 | 3 | 4;
  gap?: "sm" | "md" | "lg";
  className?: string;
}

export function GridLayout({ children, columns = 2, gap = "md", className = "" }: GridLayoutProps) {
  const cols: Record<number, string> = { 2: "grid-cols-2", 3: "grid-cols-3", 4: "grid-cols-4" };
  const gaps: Record<string, string> = { sm: "gap-4", md: "gap-6", lg: "gap-8" };
  return (
    <div className={`grid ${cols[columns]} ${gaps[gap]} ${className}`}>
      {children}
    </div>
  );
}
