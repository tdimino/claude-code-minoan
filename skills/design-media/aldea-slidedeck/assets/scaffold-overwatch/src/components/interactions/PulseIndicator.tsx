import { motion } from "motion/react";

interface PulseIndicatorProps {
  size?: number;
  color?: string;
  className?: string;
}

export function PulseIndicator({ size = 24, color = "var(--color-text-primary)", className = "" }: PulseIndicatorProps) {
  return (
    <div
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
    >
      <motion.div
        className="absolute rounded-full"
        style={{ border: `2px solid ${color}` }}
        animate={{
          width: [size * 0.4, size],
          height: [size * 0.4, size],
          opacity: [0.6, 0],
        }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
      />
      <div
        className="rounded-full"
        style={{ width: size * 0.4, height: size * 0.4, backgroundColor: color }}
      />
    </div>
  );
}
