import { useMemo } from "react";
import { motion } from "motion/react";

interface NetworkGraphProps {
  nodeCount?: number;
  rings?: number;
  color?: string;
  className?: string;
}

export function NetworkGraph({ nodeCount = 12, rings = 3, color = "var(--color-orange)", className = "" }: NetworkGraphProps) {
  const nodes = useMemo(() => Array.from({ length: nodeCount }, (_, i) => {
    const angle = (i / nodeCount) * Math.PI * 2;
    const ring = (i % rings) + 1;
    const radius = ring * 30;
    return {
      id: i,
      x: 50 + Math.cos(angle) * radius,
      y: 50 + Math.sin(angle) * radius,
      size: 4 + (rings - ring) * 2,
      delay: i * 0.1,
    };
  }), [nodeCount, rings]);

  return (
    <div className={`relative ${className}`} style={{ aspectRatio: "1/1" }}>
      {Array.from({ length: rings }, (_, i) => (
        <motion.div
          key={`ring-${i}`}
          className="absolute rounded-full border"
          style={{
            borderColor: color,
            opacity: 0.15,
            left: "50%",
            top: "50%",
            transform: "translate(-50%, -50%)",
          }}
          animate={{
            width: [(i + 1) * 60 - 10, (i + 1) * 60 + 10],
            height: [(i + 1) * 60 - 10, (i + 1) * 60 + 10],
          }}
          transition={{
            duration: 2,
            delay: i * 0.3,
            repeat: Infinity,
            repeatType: "reverse",
            ease: "easeInOut",
          }}
        />
      ))}

      <motion.div
        className="absolute rounded-full"
        style={{
          width: 10,
          height: 10,
          backgroundColor: color,
          left: "50%",
          top: "50%",
          transform: "translate(-50%, -50%)",
        }}
        animate={{ scale: [1, 1.3, 1] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      />

      {nodes.map((node) => (
        <motion.div
          key={node.id}
          className="absolute rounded-full"
          style={{
            width: node.size,
            height: node.size,
            backgroundColor: color,
            left: `${node.x}%`,
            top: `${node.y}%`,
            transform: "translate(-50%, -50%)",
          }}
          animate={{ opacity: [0.3, 0.8, 0.3] }}
          transition={{
            duration: 1.5,
            delay: node.delay,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}
