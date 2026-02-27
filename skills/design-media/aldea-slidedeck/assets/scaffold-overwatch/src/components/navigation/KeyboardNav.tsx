import { useEffect, useCallback } from "react";
import { useNavigate } from "@tanstack/react-router";

interface UseKeyboardNavOptions {
  currentSlide: number;
  totalSlides: number;
  disabled?: boolean;
}

export function useKeyboardNav({ currentSlide, totalSlides, disabled = false }: UseKeyboardNavOptions) {
  const navigate = useNavigate();

  const goToSlide = useCallback(
    (n: number) => {
      if (n >= 1 && n <= totalSlides) {
        navigate({ to: "/deck/$slide", params: { slide: String(n) } });
      }
    },
    [navigate, totalSlides]
  );

  useEffect(() => {
    if (disabled) return;

    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " ") {
        e.preventDefault();
        if (currentSlide < totalSlides) goToSlide(currentSlide + 1);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        goToSlide(currentSlide - 1);
      } else if (e.key === "Home") {
        e.preventDefault();
        goToSlide(1);
      } else if (e.key === "End") {
        e.preventDefault();
        goToSlide(totalSlides);
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [currentSlide, totalSlides, goToSlide, disabled]);

  return { goToSlide };
}
