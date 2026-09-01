import type { ReactNode } from "react";

interface EyebrowProps {
  children: ReactNode;
  className?: string;
}

export function Eyebrow({ children, className = "" }: EyebrowProps) {
  return (
    <span
      className={`inline-block text-[18px] tracking-[0.15em] uppercase font-medium ${className}`}
      style={{ fontFamily: "var(--font-body)", color: "var(--color-text-secondary)" }}
    >
      {children}
    </span>
  );
}
