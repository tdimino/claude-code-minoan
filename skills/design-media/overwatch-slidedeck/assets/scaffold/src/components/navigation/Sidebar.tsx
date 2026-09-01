import { useState, useRef, useEffect } from "react";
import { motion } from "motion/react";
import { AnimatePresence } from "motion/react";
import { config } from "../../config";

interface SidebarProps {
  slides: Array<{ number: number; shortTitle: string }>;
  currentSlide: number;
  onNavigate: (slide: number) => void;
}

export function Sidebar({ slides, currentSlide, onNavigate }: SidebarProps) {
  const [expanded, setExpanded] = useState(true);
  const collapseTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => setExpanded(false), config.navigation.autoCollapseDelay);
    return () => clearTimeout(timer);
  }, []);

  const handleEnter = () => {
    if (collapseTimer.current) {
      clearTimeout(collapseTimer.current);
      collapseTimer.current = null;
    }
    setExpanded(true);
  };

  const handleLeave = () => {
    collapseTimer.current = setTimeout(() => setExpanded(false), 300);
  };

  const total = slides.length;

  return (
    <motion.nav
      className="h-full flex flex-col rounded-r-lg shadow-2xl shrink-0"
      style={{ backgroundColor: "var(--color-bg-dark)" }}
      initial={false}
      animate={{
        width: expanded ? 280 : 40,
        borderRadius: expanded ? "0 8px 8px 0" : "0 20px 20px 0",
      }}
      transition={{ type: "spring", stiffness: 400, damping: 30, mass: 0.8 }}
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
      <AnimatePresence mode="wait">
        {expanded ? (
          <motion.div
            key="expanded"
            className="flex-1 flex flex-col min-h-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15, delay: 0.1 }}
          >
            {/* Header */}
            <div
              className="py-4 px-4 border-b flex items-center gap-3 shrink-0"
              style={{ borderColor: "var(--color-border-light)" }}
            >
              <div className="w-6 h-6 flex items-center justify-center shrink-0" style={{ color: "var(--color-primary)" }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <rect x="3" y="3" width="7" height="7" rx="1" />
                  <rect x="14" y="3" width="7" height="7" rx="1" />
                  <rect x="3" y="14" width="7" height="7" rx="1" />
                  <rect x="14" y="14" width="7" height="7" rx="1" />
                </svg>
              </div>
              <span
                className="text-white text-xs tracking-[0.15em] uppercase font-medium whitespace-nowrap"
                style={{ fontFamily: "var(--font-body)" }}
              >
                {config.title}
              </span>
            </div>

            {/* Slide list */}
            <div
              className="flex-1 min-h-0 overflow-y-auto py-2"
              style={{ scrollbarWidth: "thin", scrollbarColor: "rgba(255,255,255,0.3) transparent" }}
            >
              {slides.map((s) => {
                const active = currentSlide === s.number;
                return (
                  <button
                    key={s.number}
                    onClick={() => onNavigate(s.number)}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 transition-all relative text-left ${
                      active ? "bg-white/10" : "hover:bg-white/5"
                    }`}
                  >
                    {active && (
                      <motion.div
                        layoutId="nav-indicator"
                        className="absolute left-0 w-[3px] h-full"
                        style={{ backgroundColor: "var(--color-primary)" }}
                        transition={{ type: "spring", stiffness: 300, damping: 30 }}
                      />
                    )}
                    <span
                      className={`w-6 h-6 flex items-center justify-center text-[11px] shrink-0 rounded ${
                        active ? "text-white bg-white/10" : "text-white/40"
                      }`}
                      style={{ fontFamily: "var(--font-body)" }}
                    >
                      {String(s.number).padStart(2, "0")}
                    </span>
                    <span
                      className={`text-[11px] tracking-[0.05em] whitespace-nowrap overflow-hidden ${
                        active ? "text-white" : "text-white/60"
                      }`}
                      style={{ fontFamily: "var(--font-body)" }}
                    >
                      {s.shortTitle}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Footer */}
            <div className="py-4 px-4 border-t shrink-0" style={{ borderColor: "var(--color-border-light)" }}>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: "var(--color-primary)" }} />
                <span
                  className="text-[10px] uppercase tracking-[0.15em] text-white/40 whitespace-nowrap"
                  style={{ fontFamily: "var(--font-body)" }}
                >
                  Live Presentation
                </span>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="collapsed"
            className="flex-1 flex flex-col items-center justify-center py-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
          >
            <div className="w-8 h-8 flex items-center justify-center rounded-lg mb-3 cursor-pointer hover:bg-white/10 transition-colors" style={{ color: "var(--color-primary)" }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <rect x="3" y="3" width="7" height="7" rx="1" />
                <rect x="14" y="3" width="7" height="7" rx="1" />
                <rect x="3" y="14" width="7" height="7" rx="1" />
                <rect x="14" y="14" width="7" height="7" rx="1" />
              </svg>
            </div>
            <div
              className="text-[10px] text-white/50 font-medium"
              style={{
                fontFamily: "var(--font-body)",
                writingMode: "vertical-rl",
                textOrientation: "mixed",
                letterSpacing: "0.1em",
              }}
            >
              {String(currentSlide).padStart(2, "0")}/{total}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}
