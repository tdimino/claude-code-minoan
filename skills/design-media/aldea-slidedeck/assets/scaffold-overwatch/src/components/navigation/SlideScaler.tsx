import { useRef, useState, useLayoutEffect, type ReactNode } from "react";
import { config } from "../../config";

const { width: DESIGN_W, height: DESIGN_H } = config.design;

interface SlideScalerProps {
  children: ReactNode;
}

export function SlideScaler({ children }: SlideScalerProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState<number | null>(null);

  useLayoutEffect(() => {
    if (!ref.current) return;
    const container = ref.current.parentElement;
    if (!container) return;

    const measure = () => {
      const cw = container.clientWidth - 32;
      const ch = container.clientHeight - 32;
      const sx = cw / DESIGN_W;
      const sy = ch / DESIGN_H;
      setScale(Math.min(sx, sy));
    };

    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      style={{
        width: scale ? DESIGN_W * scale : "100%",
        height: scale ? DESIGN_H * scale : "100%",
        opacity: scale ? 1 : 0,
      }}
    >
      {scale && (
        <div
          className="bg-white shadow-2xl overflow-hidden relative"
          style={{
            width: DESIGN_W,
            height: DESIGN_H,
            transform: `scale(${scale})`,
            transformOrigin: "top left",
            borderRadius: 4,
            containerType: "size",
          }}
        >
          {children}
        </div>
      )}
    </div>
  );
}
