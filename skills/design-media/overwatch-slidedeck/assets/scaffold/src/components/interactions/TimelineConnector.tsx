import { motion } from "motion/react";

interface Phase {
  label: string;
  subtitle?: string;
  description?: string;
  status: "complete" | "current" | "upcoming";
}

interface TimelineConnectorProps {
  phases: Phase[];
  className?: string;
}

export function TimelineConnector({ phases, className }: TimelineConnectorProps) {
  return (
    <div className={className}>
      <div
        className="grid w-full relative z-10"
        style={{ gridTemplateColumns: `repeat(${phases.length}, 1fr)`, gap: "2rem" }}
      >
        {phases.map((phase, i) => (
          <motion.div
            key={phase.label}
            className="flex flex-col items-center relative w-full"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 + i * 0.15, duration: 0.4, ease: "easeOut" }}
          >
            {/* Phase subtitle */}
            {phase.subtitle && (
              <span
                className="text-[13px] tracking-[0.15em] uppercase h-6 flex items-center mb-4"
                style={{
                  fontFamily: "var(--font-mono)",
                  color: phase.status === "current" ? "var(--color-orange)" : "var(--color-text-muted)",
                }}
              >
                {phase.subtitle}
              </span>
            )}

            {/* Connector line to next phase */}
            {i < phases.length - 1 && (
              <>
                <motion.div
                  className="absolute z-0"
                  style={{
                    top: phase.subtitle ? "47px" : "8px",
                    left: "50%",
                    width: "calc(100% + 2rem)",
                    height: "2px",
                    backgroundColor: "var(--color-border-light)",
                    transformOrigin: "left",
                  }}
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ delay: 0.8 + i * 0.15, duration: 0.5, ease: "easeInOut" }}
                />
                {/* Chevron arrow */}
                <motion.div
                  className="absolute z-10 flex items-center justify-center bg-[var(--color-bg-primary)] px-1"
                  style={{
                    top: phase.subtitle ? "48px" : "9px",
                    left: "calc(100% + 1rem)",
                    color: "var(--color-text-muted)",
                    transform: "translate(-50%, -50%)",
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.1 + i * 0.1, duration: 0.3 }}
                >
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="m9 18 6-6-6-6" />
                  </svg>
                </motion.div>
              </>
            )}

            {/* Phase dot */}
            <div
              className="w-[16px] h-[16px] rounded-full relative z-10"
              style={{
                backgroundColor:
                  phase.status === "current"
                    ? "var(--color-orange)"
                    : phase.status === "complete"
                      ? "var(--color-text-muted)"
                      : "var(--color-bg-primary)",
                border:
                  phase.status === "upcoming"
                    ? "2px solid var(--color-border-light)"
                    : "none",
                boxShadow:
                  phase.status === "current"
                    ? "0 0 16px rgba(255, 110, 65, 0.5)"
                    : "none",
              }}
            />

            {/* Phase card */}
            <motion.div
              className="mt-8 p-6 w-full flex-1 flex flex-col items-start text-left"
              style={{
                border:
                  phase.status === "current"
                    ? "1.5px solid var(--color-orange)"
                    : "1.5px solid var(--color-border-light)",
                borderRadius: "var(--radius-lg)",
                backgroundColor:
                  phase.status === "current"
                    ? "rgba(255, 110, 65, 0.06)"
                    : "rgba(255, 255, 255, 0.01)",
              }}
              whileHover={{
                borderColor:
                  phase.status === "current" ? "var(--color-orange)" : "rgba(255, 255, 255, 0.3)",
                y: -4,
              }}
            >
              <span
                className="text-[20px] leading-[1.1] uppercase block"
                style={{
                  fontFamily: "var(--font-heading)",
                  color: "var(--color-text-primary)",
                }}
              >
                {phase.label}
              </span>
              {phase.description && (
                <span
                  className="text-[15px] leading-[1.5] block mt-4"
                  style={{
                    fontFamily: "var(--font-body)",
                    color: "var(--color-text-muted)",
                  }}
                >
                  {phase.description}
                </span>
              )}
            </motion.div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
