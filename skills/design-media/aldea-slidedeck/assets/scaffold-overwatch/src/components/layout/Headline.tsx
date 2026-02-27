import type { ReactNode } from "react";

interface HeadlineProps {
  children: ReactNode;
  className?: string;
}

export function Headline({ children, className = "" }: HeadlineProps) {
  return (
    <h1
      className={`text-[140px] leading-[0.85] tracking-[-0.02em] uppercase ${className}`}
      style={{ fontFamily: "var(--font-heading)", color: "var(--color-text-primary)" }}
    >
      {children}
    </h1>
  );
}
