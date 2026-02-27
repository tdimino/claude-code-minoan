import { useState, useEffect, useCallback, useRef } from "react";

/**
 * Generic auto-advancing timer hook.
 * Returns [currentItem, currentIndex, setIndex].
 * Timer resets when index is manually set.
 */
export function useAutoCycle<T>(items: T[], interval: number): [T, number, (i: number) => void] {
  const [index, setIndex] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (items.length <= 1) return;
    timerRef.current = setInterval(() => {
      setIndex((i) => (i + 1) % items.length);
    }, interval);
  }, [items.length, interval]);

  useEffect(() => {
    startTimer();
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [startTimer]);

  const set = useCallback(
    (i: number) => {
      setIndex(Math.max(0, Math.min(i, items.length - 1)));
      startTimer();
    },
    [items.length, startTimer],
  );

  return [items[index], index, set];
}
