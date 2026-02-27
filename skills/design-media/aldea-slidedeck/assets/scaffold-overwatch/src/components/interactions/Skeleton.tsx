import { motion } from "motion/react";

interface SkeletonProps {
  width?: number | string;
  height?: number;
  className?: string;
}

export function Skeleton({ width, height = 20, className = "" }: SkeletonProps) {
  return (
    <motion.div
      className={className}
      style={{
        width: width ?? "100%",
        height,
        backgroundColor: "var(--color-bg-secondary)",
      }}
      animate={{ opacity: [0.4, 0.7, 0.4] }}
      transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}
