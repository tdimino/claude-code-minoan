interface DividerProps {
  className?: string;
  thickness?: "thin" | "medium" | "thick";
}

export function Divider({ className = "", thickness = "thin" }: DividerProps) {
  const heights = { thin: "h-px", medium: "h-0.5", thick: "h-1" };
  return (
    <div
      className={`${heights[thickness]} w-full ${className}`}
      style={{ backgroundColor: "var(--color-border)" }}
    />
  );
}
