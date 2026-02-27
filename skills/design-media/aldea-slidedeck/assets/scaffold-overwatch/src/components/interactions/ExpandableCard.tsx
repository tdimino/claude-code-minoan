import { useState, useRef, useCallback, useEffect, type ReactNode } from "react";
import { motion, AnimatePresence } from "motion/react";

interface ExpandableCardProps {
  preview: ReactNode;
  detail: ReactNode;
  className?: string;
}

export function ExpandableCard({ preview, detail, className = "" }: ExpandableCardProps) {
  const [expanded, setExpanded] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (ref.current && !ref.current.contains(e.target as Node)) {
      setExpanded(false);
    }
  }, []);

  useEffect(() => {
    if (expanded) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [expanded, handleClickOutside]);

  return (
    <motion.div
      ref={ref}
      layout
      onClick={() => setExpanded((v) => !v)}
      className={`cursor-pointer overflow-hidden ${className}`}
      style={{
        boxShadow: expanded ? "var(--shadow-xl)" : "none",
        borderRadius: expanded ? "var(--radius-lg)" : "0",
      }}
      transition={{ layout: { duration: 0.3, ease: "easeOut" } }}
    >
      <motion.div layout="position">{preview}</motion.div>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="overflow-hidden"
          >
            {detail}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
