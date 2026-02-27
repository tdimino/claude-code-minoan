import type { ReactNode } from "react";
import { motion, useMotionValue, useMotionTemplate } from "motion/react";

interface GlowBorderProps {
  children: ReactNode;
  color?: string;
  radius?: number;
  borderWidth?: number;
  className?: string;
}

export function GlowBorder({
  children,
  color = "var(--color-orange)",
  radius = 500,
  borderWidth = 3,
  className = "",
}: GlowBorderProps) {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent<HTMLDivElement>) {
    const rect = currentTarget.getBoundingClientRect();
    const scaleX = currentTarget.offsetWidth / rect.width;
    const scaleY = currentTarget.offsetHeight / rect.height;
    mouseX.set((clientX - rect.left) * scaleX);
    mouseY.set((clientY - rect.top) * scaleY);
  }

  const background = useMotionTemplate`radial-gradient(${radius}px circle at ${mouseX}px ${mouseY}px, ${color}, transparent 70%)`;

  return (
    <div className={`relative group ${className}`} onMouseMove={handleMouseMove}>
      <motion.div
        className="absolute pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{ inset: `-${borderWidth}px`, background }}
      />
      <div className="relative">{children}</div>
    </div>
  );
}
