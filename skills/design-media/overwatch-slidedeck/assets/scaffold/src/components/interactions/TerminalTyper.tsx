import { useState, useEffect } from "react";
import { useTypewriter } from "../../hooks/useTypewriter";

interface TerminalTyperProps {
  /** Lines to type sequentially. Each line types after the previous completes. */
  lines: string[];
  /** Milliseconds per character. Default 35. */
  typingSpeed?: number;
  /** Milliseconds before first line starts typing. Default 300. */
  startDelay?: number;
  /** Shell prompt character. Default "$". */
  prompt?: string;
  /** Called when all lines have finished typing. */
  onComplete?: () => void;
  className?: string;
}

function BlinkingCursor({ visible }: { visible: boolean }) {
  const [on, setOn] = useState(true);

  useEffect(() => {
    if (!visible) return;
    const timer = setInterval(() => setOn((v) => !v), 530);
    return () => clearInterval(timer);
  }, [visible]);

  if (!visible) return null;
  return (
    <span
      className="inline-block w-[10px] h-[20px] ml-px align-middle"
      style={{ backgroundColor: on ? "var(--color-orange)" : "transparent" }}
    />
  );
}

function TypewriterLine({
  text,
  speed,
  delay,
  onComplete,
}: {
  text: string;
  speed: number;
  delay: number;
  onComplete?: () => void;
}) {
  const { displayText, isComplete } = useTypewriter(text, speed, delay);

  useEffect(() => {
    if (isComplete && onComplete) onComplete();
  }, [isComplete, onComplete]);

  return (
    <>
      <span style={{ color: "var(--color-text-muted)" }}>{displayText}</span>
      <BlinkingCursor visible={!isComplete} />
    </>
  );
}

export function TerminalTyper({
  lines,
  typingSpeed = 35,
  startDelay = 300,
  prompt = "$",
  onComplete,
  className,
}: TerminalTyperProps) {
  const [activeLine, setActiveLine] = useState(0);

  // Reset when lines prop changes
  useEffect(() => {
    setActiveLine(0);
  }, [lines]);

  // Calculate cumulative delays for sequential typing
  const getDelay = (index: number) => {
    if (index === 0) return startDelay;
    // Each subsequent line starts after the previous finishes + a small gap
    let total = startDelay;
    for (let i = 0; i < index; i++) {
      total += lines[i].length * typingSpeed + 400;
    }
    return total;
  };

  return (
    <div
      className={className}
      style={{
        backgroundColor: "rgba(255, 255, 255, 0.03)",
        border: "1px solid var(--color-border-light)",
        borderRadius: "var(--radius-lg)",
        fontFamily: "var(--font-mono)",
        padding: "24px",
      }}
    >
      {/* macOS window chrome */}
      <div className="flex items-center gap-2 mb-4">
        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: "#FF5F57" }} />
        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: "#FEBC2E" }} />
        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: "#28C840" }} />
      </div>

      {/* Lines */}
      <div className="text-[22px] leading-[1.8] tracking-[0.02em]">
        {lines.map((line, i) => (
          <div key={i}>
            {i <= activeLine && (
              <TypewriterLine
                text={`${prompt} ${line}`}
                speed={typingSpeed}
                delay={getDelay(i)}
                onComplete={() => {
                  if (i === activeLine && i < lines.length - 1) {
                    setActiveLine(i + 1);
                  }
                  if (i === lines.length - 1 && onComplete) {
                    onComplete();
                  }
                }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
