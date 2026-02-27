interface SlideCounterProps {
  current: number;
  total: number;
}

export function SlideCounter({ current, total }: SlideCounterProps) {
  return (
    <div
      className="absolute bottom-[20px] right-[24px] text-[11px] tracking-[0.1em]"
      style={{ fontFamily: "var(--font-mono)", color: "#999" }}
    >
      {String(current).padStart(2, "0")}/{String(total).padStart(2, "0")}
    </div>
  );
}
