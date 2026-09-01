import type { ReactNode } from "react";
import { motion, AnimatePresence } from "motion/react";
import { useAutoCycle } from "../../hooks/useAutoCycle";
import { useReducedMotion } from "../../hooks/useReducedMotion";

interface ContentRotatorProps {
  children: ReactNode[];
  interval?: number;
  showDots?: boolean;
  dotColor?: string;
  className?: string;
}

export function ContentRotator({
  children,
  interval = 5000,
  showDots = true,
  dotColor = "var(--color-text-primary)",
  className,
}: ContentRotatorProps) {
  const [, index, setIndex] = useAutoCycle(children, interval);
  const prefersReduced = useReducedMotion();

  return (
    <div className={className}>
      <div className="relative overflow-hidden" style={{ minHeight: "4em" }}>
        {prefersReduced ? (
          <div>{children[index]}</div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              {children[index]}
            </motion.div>
          </AnimatePresence>
        )}
      </div>

      {showDots && children.length > 1 && (
        <div className="flex gap-1.5 mt-4">
          {children.map((_, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setIndex(i)}
              className="h-1 rounded-full transition-all duration-300 cursor-pointer"
              style={{
                width: i === index ? 20 : 6,
                backgroundColor: i === index ? dotColor : "var(--color-border-light)",
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
