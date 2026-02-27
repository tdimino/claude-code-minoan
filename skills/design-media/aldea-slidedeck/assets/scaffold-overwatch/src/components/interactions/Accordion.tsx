import { useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "motion/react";

interface AccordionProps {
  trigger: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
}

export function Accordion({ trigger, children, defaultOpen = false, className = "" }: AccordionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={`border-b ${className}`} style={{ borderColor: "var(--color-border-light)" }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between py-5 text-left cursor-pointer"
      >
        <span>{trigger}</span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-[24px] leading-none select-none"
          style={{ color: "var(--color-text-muted)" }}
        >
          ↓
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="overflow-hidden"
          >
            <div className="pb-5">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
