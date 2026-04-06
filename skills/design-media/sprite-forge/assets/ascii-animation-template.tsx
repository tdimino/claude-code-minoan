"use client";
import { useState, useEffect, useRef } from "react";

interface AsciiAnimationProps {
  isPlaying?: boolean;
}

const APPEARANCE = {
  useColors: true,
  textEffectThreshold: 0.6,
  textEffect: "video" as "video" | "gradient" | "burn",
};

const CHARS = "·•●⬤";
const FPS = 30;

// Replace with your frame data — each string is one animation frame
const FRAMES: string[] = [
  `   ·····   \n  ·     ·  \n ·       · \n·         ·\n ·       · \n  ·     ·  \n   ·····   `,
  `   •••••   \n  •     •  \n •       • \n•         •\n •       • \n  •     •  \n   •••••   `,
  `   ●●●●●   \n  ●     ●  \n ●       ● \n●         ●\n ●       ● \n  ●     ●  \n   ●●●●●   `,
];

export default function AsciiAnimation({ isPlaying = true }: AsciiAnimationProps) {
  const [frameIndex, setFrameIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setFrameIndex((prev) => (prev + 1) % FRAMES.length);
    }, 1000 / FPS);
    return () => clearInterval(interval);
  }, [isPlaying]);

  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const width = entry.contentRect.width;
        const fontSize = Math.max(4, Math.min(12, width / 80));
        if (containerRef.current) {
          containerRef.current.style.fontSize = `${fontSize}px`;
        }
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        fontFamily: "monospace",
        whiteSpace: "pre",
        lineHeight: 1.2,
        color: "#e0e0e0",
        background: "#0a0a0a",
        padding: "1rem",
        borderRadius: "0.5rem",
      }}
    >
      {FRAMES[frameIndex]}
    </div>
  );
}
