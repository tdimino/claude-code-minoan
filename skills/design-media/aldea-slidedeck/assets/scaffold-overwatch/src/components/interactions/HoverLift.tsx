import type { ReactNode } from "react";
import { motion } from "motion/react";

interface HoverLiftProps {
  children: ReactNode;
  lift?: "sm" | "md" | "lg";
  shadow?: boolean;
  scale?: boolean;
  className?: string;
}

const lifts = { sm: -4, md: -8, lg: -12 };

export function HoverLift({ children, lift = "md", shadow = true, scale: doScale = false, className }: HoverLiftProps) {
  return (
    <motion.div
      whileHover={{
        y: lifts[lift],
        scale: doScale ? 1.02 : 1,
        boxShadow: shadow ? "var(--shadow-md)" : "none",
      }}
      transition={{ duration: 0.2 }}
      className={className}
      style={{ borderRadius: "var(--radius-sm)" }}
    >
      {children}
    </motion.div>
  );
}
