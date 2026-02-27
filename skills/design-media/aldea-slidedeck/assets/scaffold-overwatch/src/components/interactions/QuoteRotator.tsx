import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";

interface Quote {
  text: string;
  attribution?: string;
}

interface QuoteRotatorProps {
  quotes: Quote[];
  interval?: number;
  className?: string;
}

export function QuoteRotator({ quotes, interval = 5000, className = "" }: QuoteRotatorProps) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % quotes.length);
    }, interval);
    return () => clearInterval(timer);
  }, [quotes.length, interval]);

  const current = quotes[index];

  return (
    <div className={className}>
      <div className="relative overflow-hidden" style={{ minHeight: "4em" }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={index}
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.04 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          >
            <p
              className="text-[28px] leading-[1.3] uppercase"
              style={{ fontFamily: "var(--font-heading)", color: "var(--color-text-primary)" }}
            >
              &ldquo;{current.text}&rdquo;
            </p>
            {current.attribution && (
              <p
                className="text-[16px] mt-3"
                style={{ fontFamily: "var(--font-mono)", color: "var(--color-text-muted)" }}
              >
                &mdash; {current.attribution}
              </p>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
      {quotes.length > 1 && (
        <div className="flex gap-2 mt-4">
          {quotes.map((_, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setIndex(i)}
              className="h-[6px] transition-all duration-300 cursor-pointer"
              style={{
                width: i === index ? 32 : 6,
                backgroundColor: i === index ? "var(--color-text-primary)" : "var(--color-border-light)",
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
