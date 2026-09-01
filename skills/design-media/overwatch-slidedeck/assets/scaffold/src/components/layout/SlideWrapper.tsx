import type { ReactNode } from "react";

interface SlideWrapperProps {
  children: ReactNode;
  className?: string;
  mode?: "dark" | "white" | "orange";
}

export function SlideWrapper({ children, className = "", mode = "dark" }: SlideWrapperProps) {
  return (
    <div
      className={`w-full h-full p-[64px] overflow-hidden relative ${className}`}
      data-slide-mode={mode}
      style={{ backgroundColor: "var(--color-bg-primary)", color: "var(--color-text-primary)" }}
    >
      {children}
    </div>
  );
}
