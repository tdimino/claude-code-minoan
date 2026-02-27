import { useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "motion/react";

interface TabItem {
  label: string;
  content: ReactNode;
}

interface TabGroupProps {
  items: TabItem[];
  className?: string;
}

export function TabGroup({ items, className = "" }: TabGroupProps) {
  const [active, setActive] = useState(0);

  return (
    <div className={className}>
      <div className="flex gap-0 border-b" style={{ borderColor: "var(--color-border-light)" }}>
        {items.map((item, i) => (
          <button
            key={i}
            type="button"
            onClick={() => setActive(i)}
            className="px-5 py-3 text-[16px] tracking-[0.1em] uppercase cursor-pointer transition-colors duration-200"
            style={{
              fontFamily: "var(--font-mono)",
              color: i === active ? "var(--color-text-primary)" : "var(--color-text-muted)",
              backgroundColor: "transparent",
              borderBottom: i === active ? "2px solid var(--color-text-primary)" : "2px solid transparent",
            }}
          >
            {item.label}
          </button>
        ))}
      </div>
      <AnimatePresence mode="wait">
        <motion.div
          key={active}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className="pt-6"
        >
          {items[active].content}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
