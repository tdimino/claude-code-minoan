import type { ReactNode } from "react";
import { motion } from "motion/react";

interface StaggeredAnimationProps {
  children: ReactNode;
  stagger?: number;
  delay?: number;
  className?: string;
}

export function StaggeredAnimation({ children, stagger = 0.1, delay = 0.2, className }: StaggeredAnimationProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: { staggerChildren: stagger, delayChildren: delay },
        },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
