import { config } from "../../config";

export function MobileBlock() {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-6"
      style={{ backgroundColor: "var(--color-bg-cream)" }}
    >
      <div className="text-center max-w-sm">
        <div className="flex justify-center mb-6">
          <div className="relative">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ccc" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="5" y="2" width="14" height="20" rx="2" ry="2" />
              <line x1="12" y1="18" x2="12.01" y2="18" />
            </svg>
            <div
              className="absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center text-white text-xs font-bold"
              style={{ backgroundColor: "var(--color-primary)" }}
            >
              ✕
            </div>
          </div>
        </div>
        <h1 className="text-xl mb-3" style={{ fontFamily: "var(--font-heading)" }}>
          Desktop Required
        </h1>
        <p className="text-[12px] mb-6 leading-relaxed" style={{ fontFamily: "var(--font-body)", color: "var(--color-text-muted)" }}>
          This presentation is optimized for larger screens. Please view on a desktop or laptop.
        </p>
        <div className="flex items-center justify-center gap-2 text-[10px] uppercase tracking-[0.2em]" style={{ color: "#999", fontFamily: "var(--font-body)" }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
            <line x1="8" y1="21" x2="16" y2="21" />
            <line x1="12" y1="17" x2="12" y2="21" />
          </svg>
          <span>Min width: {config.design.minViewportWidth}px</span>
        </div>
      </div>
    </div>
  );
}
