import { motion } from "motion/react";

interface ProgressBarProps {
  /** Current value. */
  value: number;
  /** Maximum value. Default 100. */
  max?: number;
  /** Bar fill color. Default "var(--color-orange)". */
  color?: string;
  /** Optional label above the bar. */
  label?: string;
  /** Whether to animate the fill. Default true. */
  animate?: boolean;
  /** Animation delay in seconds. Default 0. */
  delay?: number;
  /** Bar height. Default "6px". */
  height?: string;
  className?: string;
}

export function ProgressBar({
  value,
  max = 100,
  color = "var(--color-orange)",
  label,
  animate = true,
  delay = 0,
  height = "6px",
  className,
}: ProgressBarProps) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={className}>
      {label && (
        <div className="flex justify-between items-end mb-1.5">
          <span
            className="text-[13px] uppercase tracking-wider"
            style={{ fontFamily: "var(--font-mono)", color: "var(--color-text-muted)" }}
          >
            {label}
          </span>
          <span
            className="text-[13px] font-bold"
            style={{ fontFamily: "var(--font-mono)", color: "var(--color-text-primary)" }}
          >
            {Math.round(pct)}%
          </span>
        </div>
      )}
      <div
        className="w-full rounded-full overflow-hidden"
        style={{ height, backgroundColor: "var(--color-border-light)" }}
      >
        {animate ? (
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: color }}
            initial={{ width: 0 }}
            animate={{ width: `${pct}%` }}
            transition={{ delay, duration: 0.8, ease: "easeOut" }}
          />
        ) : (
          <div
            className="h-full rounded-full"
            style={{ backgroundColor: color, width: `${pct}%` }}
          />
        )}
      </div>
    </div>
  );
}
