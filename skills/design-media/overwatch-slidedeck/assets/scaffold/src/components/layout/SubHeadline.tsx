import type { ReactNode, CSSProperties } from "react";

interface SubHeadlineProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}

export function SubHeadline({ children, className = "", style }: SubHeadlineProps) {
  return (
    <h2
      className={`text-[72px] leading-[0.9] tracking-[-0.01em] uppercase ${className}`}
      style={{ fontFamily: "var(--font-heading)", color: "var(--color-text-primary)", ...style }}
    >
      {children}
    </h2>
  );
}
