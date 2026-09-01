import type { ReactNode } from "react";
import { motion } from "motion/react";
import { useReducedMotion } from "../../hooks/useReducedMotion";

interface InfiniteScrollTickerProps {
  children: ReactNode;
  speed?: number;
  direction?: "up" | "down";
  height?: string | number;
  className?: string;
}

export function InfiniteScrollTicker({
  children,
  speed = 8,
  direction = "up",
  height = "100%",
  className,
}: InfiniteScrollTickerProps) {
  const prefersReduced = useReducedMotion();
  const yStart = direction === "up" ? "0%" : "-50%";
  const yEnd = direction === "up" ? "-50%" : "0%";

  return (
    <div
      className={`relative overflow-hidden ${className ?? ""}`}
      style={{ height }}
    >
      <div
        className="absolute inset-x-0 top-0 h-10 z-10 pointer-events-none"
        style={{
          background: "linear-gradient(to bottom, var(--color-bg-primary) 0%, transparent 100%)",
        }}
      />

      <div
        className="absolute inset-x-0 bottom-0 h-12 z-10 pointer-events-none"
        style={{
          background: "linear-gradient(to top, var(--color-bg-primary) 0%, transparent 100%)",
        }}
      />

      {prefersReduced ? (
        <div>{children}</div>
      ) : (
        <motion.div
          animate={{ y: [yStart, yEnd] }}
          transition={{
            duration: speed,
            ease: "linear",
            repeat: Infinity,
          }}
        >
          {children}
          {children}
        </motion.div>
      )}
    </div>
  );
}
