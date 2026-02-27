import { useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "motion/react";

interface TooltipProps {
  children: ReactNode;
  content: ReactNode;
  position?: "top" | "bottom";
  className?: string;
}

export function Tooltip({ children, content, position = "top", className = "" }: TooltipProps) {
  const [visible, setVisible] = useState(false);

  return (
    <div
      className={`relative inline-block ${className}`}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      <AnimatePresence>
        {visible && (
          <motion.div
            initial={{ opacity: 0, y: position === "top" ? 4 : -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: position === "top" ? 4 : -4 }}
            transition={{ duration: 0.15 }}
            className="absolute left-1/2 -translate-x-1/2 z-50 px-3 py-2 whitespace-nowrap"
            style={{
              [position === "top" ? "bottom" : "top"]: "calc(100% + 8px)",
              backgroundColor: "var(--color-bg-dark, #0A0A0A)",
              color: "var(--color-text-inverse, #FFFFFF)",
              fontFamily: "var(--font-mono)",
              fontSize: "14px",
              border: "1px solid var(--color-border-light)",
            }}
          >
            {content}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
