import type { ReactNode } from "react";
import { motion } from "motion/react";

interface InfiniteScrollTickerProps {
  children: ReactNode;
  /** Animation duration in seconds for one full cycle. Default 8. */
  speed?: number;
  /** Scroll direction. Default "up". */
  direction?: "up" | "down";
  /** Height of the visible area. Default "100%". */
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
  const yStart = direction === "up" ? "0%" : "-50%";
  const yEnd = direction === "up" ? "-50%" : "0%";

  return (
    <div
      className={`relative overflow-hidden ${className ?? ""}`}
      style={{ height }}
    >
      {/* Top gradient mask */}
      <div
        className="absolute inset-x-0 top-0 h-10 z-10 pointer-events-none"
        style={{
          background: "linear-gradient(to bottom, var(--color-bg-primary) 0%, transparent 100%)",
        }}
      />

      {/* Bottom gradient mask */}
      <div
        className="absolute inset-x-0 bottom-0 h-12 z-10 pointer-events-none"
        style={{
          background: "linear-gradient(to top, var(--color-bg-primary) 0%, transparent 100%)",
        }}
      />

      {/* Scrolling content — duplicated for seamless loop */}
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
    </div>
  );
}
