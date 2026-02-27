import { useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "motion/react";

interface RevealCaptionProps {
  children: ReactNode;
  caption: ReactNode;
  position?: "top" | "bottom";
  className?: string;
}

export function RevealCaption({ children, caption, position = "bottom", className = "" }: RevealCaptionProps) {
  const [hovered, setHovered] = useState(false);
  const isTop = position === "top";

  return (
    <div
      className={`relative overflow-hidden ${className}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {children}
      <AnimatePresence>
        {hovered && (
          <motion.div
            initial={{ y: isTop ? "-100%" : "100%" }}
            animate={{ y: 0 }}
            exit={{ y: isTop ? "-100%" : "100%" }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="absolute inset-x-0 p-4"
            style={{
              [isTop ? "top" : "bottom"]: 0,
              backgroundColor: "rgba(0, 0, 0, 0.85)",
              color: "#FFFFFF",
            }}
          >
            {caption}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
