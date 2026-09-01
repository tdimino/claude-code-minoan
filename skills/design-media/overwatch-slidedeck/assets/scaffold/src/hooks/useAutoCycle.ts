import { useState, useEffect, useCallback, useRef } from "react";
import { useReducedMotion } from "./useReducedMotion";

export function useAutoCycle<T>(items: T[], interval: number): [T, number, (i: number) => void] {
  const [index, setIndex] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prefersReduced = useReducedMotion();

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startTimer = useCallback(() => {
    clearTimer();
    if (prefersReduced || items.length <= 1) return;
    timerRef.current = setInterval(() => {
      setIndex((i) => (i + 1) % items.length);
    }, interval);
  }, [items.length, interval, prefersReduced, clearTimer]);

  useEffect(() => {
    startTimer();
    return clearTimer;
  }, [startTimer, clearTimer]);

  useEffect(() => {
    const onVisibility = () => {
      if (document.hidden) clearTimer();
      else startTimer();
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [startTimer, clearTimer]);

  const set = useCallback(
    (i: number) => {
      setIndex(Math.max(0, Math.min(i, items.length - 1)));
      startTimer();
    },
    [items.length, startTimer],
  );

  return [items[index], index, set];
}
