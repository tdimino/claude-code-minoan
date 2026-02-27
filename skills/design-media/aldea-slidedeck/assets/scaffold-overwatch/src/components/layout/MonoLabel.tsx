import type { ReactNode } from "react";

interface MonoLabelProps {
  children: ReactNode;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function MonoLabel({ children, className = "", size = "md" }: MonoLabelProps) {
  const sizes = { sm: "text-[14px]", md: "text-[18px]", lg: "text-[22px]" };
  return (
    <span
      className={`${sizes[size]} tracking-[0.1em] uppercase ${className}`}
      style={{ fontFamily: "var(--font-mono)", color: "var(--color-text-muted)" }}
    >
      {children}
    </span>
  );
}
