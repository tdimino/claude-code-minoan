import { useState, useEffect } from "react";

/**
 * Character-by-character text reveal hook.
 * Returns { displayText, isComplete }.
 */
export function useTypewriter(
  text: string,
  speed: number = 35,
  delay: number = 0,
): { displayText: string; isComplete: boolean } {
  const [displayText, setDisplayText] = useState("");

  useEffect(() => {
    setDisplayText("");
    let charIndex = 0;
    let interval: ReturnType<typeof setInterval>;

    const timeout = setTimeout(() => {
      interval = setInterval(() => {
        charIndex++;
        setDisplayText(text.slice(0, charIndex));
        if (charIndex >= text.length) clearInterval(interval);
      }, speed);
    }, delay);

    return () => {
      clearTimeout(timeout);
      if (interval) clearInterval(interval);
      setDisplayText("");
    };
  }, [text, speed, delay]);

  return { displayText, isComplete: text.length === 0 || displayText.length >= text.length };
}
