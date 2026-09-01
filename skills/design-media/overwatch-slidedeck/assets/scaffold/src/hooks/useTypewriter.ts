import { useState, useEffect, useRef } from "react";
import { useReducedMotion } from "./useReducedMotion";

export function useTypewriter(
  text: string,
  speed: number = 35,
  delay: number = 0,
): { displayText: string; isComplete: boolean } {
  const prefersReduced = useReducedMotion();
  const [displayText, setDisplayText] = useState("");
  const charRef = useRef(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (prefersReduced) {
      setDisplayText(text);
      return;
    }

    setDisplayText("");
    charRef.current = 0;

    timeoutRef.current = setTimeout(() => {
      timeoutRef.current = null;
      intervalRef.current = setInterval(() => {
        charRef.current++;
        setDisplayText(text.slice(0, charRef.current));
        if (charRef.current >= text.length) {
          if (intervalRef.current) clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      }, speed);
    }, delay);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (intervalRef.current) clearInterval(intervalRef.current);
      timeoutRef.current = null;
      intervalRef.current = null;
    };
  }, [text, speed, delay, prefersReduced]);

  useEffect(() => {
    if (prefersReduced) return;

    const onVisibility = () => {
      if (document.hidden) {
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = null;
      } else if (charRef.current < text.length && !intervalRef.current) {
        intervalRef.current = setInterval(() => {
          charRef.current++;
          setDisplayText(text.slice(0, charRef.current));
          if (charRef.current >= text.length) {
            if (intervalRef.current) clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }, speed);
      }
    };

    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [text, speed, prefersReduced]);

  return { displayText, isComplete: text.length === 0 || displayText.length >= text.length };
}
