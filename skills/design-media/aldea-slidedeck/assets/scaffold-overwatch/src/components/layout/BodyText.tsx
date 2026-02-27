import type { ReactNode } from "react";

interface BodyTextProps {
  children: ReactNode;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function BodyText({ children, className = "", size = "md" }: BodyTextProps) {
  const sizes = {
    sm: "text-[20px] leading-[1.5]",
    md: "text-[24px] leading-[1.6]",
    lg: "text-[28px] leading-[1.6]",
  };
  return (
    <p
      className={`${sizes[size]} ${className}`}
      style={{ fontFamily: "var(--font-body)", color: "var(--color-text-secondary)" }}
    >
      {children}
    </p>
  );
}
