import { useMemo, useRef, useState, useEffect } from "react";
import { motion } from "motion/react";

interface ParticleFieldProps {
  count?: number;
  color?: string;
  className?: string;
}

export function ParticleField({ count = 20, color = "var(--color-orange)", className = "" }: ParticleFieldProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(800);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      setHeight(entry.contentRect.height || 800);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const particles = useMemo(
    () =>
      Array.from({ length: count }, (_, i) => ({
        id: i,
        x: Math.random() * 100,
        startY: Math.random() * 100,
        size: 2 + Math.random() * 4,
        duration: 4 + Math.random() * 6,
        delay: Math.random() * 5,
        opacity: 0.2 + Math.random() * 0.5,
      })),
    [count]
  );

  return (
    <div ref={containerRef} className={`absolute inset-0 overflow-hidden pointer-events-none ${className}`}>
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute rounded-full"
          style={{
            left: `${p.x}%`,
            bottom: 0,
            width: p.size,
            height: p.size,
            backgroundColor: color,
          }}
          animate={{
            y: [0, -(height + p.size)],
            opacity: [0, p.opacity, 0],
          }}
          transition={{
            duration: p.duration,
            delay: p.delay,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      ))}
    </div>
  );
}
