import { Suspense, useEffect, useRef, useMemo } from "react";
import { useParams, useNavigate, useSearch } from "@tanstack/react-router";
import { AnimatePresence, motion } from "motion/react";
import {
  config,
  slides as slideRegistry,
  totalSlides,
  getSlideComponent,
  preloadSlide,
  slideList,
  type TransitionType,
} from "../config";
import { DeckShell } from "../components/chrome/DeckShell";

let prevSlideRef = 0;

function useReducedMotionInline(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function getTransitionVariants(
  type: TransitionType,
  direction: number,
  duration: number,
) {
  const durationSec = duration / 1000;
  const ease = [0.4, 0, 0.2, 1] as const;

  switch (type) {
    case "slide":
      return {
        initial: { x: direction > 0 ? "100%" : "-100%", opacity: 0 },
        animate: { x: 0, opacity: 1, transition: { duration: durationSec, ease } },
        exit: { x: direction > 0 ? "-100%" : "100%", opacity: 0, transition: { duration: durationSec, ease } },
      };
    case "scale":
      return {
        initial: { scale: direction > 0 ? 1.05 : 0.95, opacity: 0 },
        animate: { scale: 1, opacity: 1, transition: { duration: durationSec, ease } },
        exit: { scale: direction > 0 ? 0.95 : 1.05, opacity: 0, transition: { duration: durationSec, ease } },
      };
    case "fade":
      return {
        initial: { opacity: 0 },
        animate: { opacity: 1, transition: { duration: durationSec, ease } },
        exit: { opacity: 0, transition: { duration: durationSec, ease } },
      };
    case "none":
    default:
      return {
        initial: {},
        animate: {},
        exit: {},
      };
  }
}

export function SlideRoute() {
  const { slide } = useParams({ strict: false }) as { slide: string };
  const navigate = useNavigate();
  const search = useSearch({ strict: false }) as Record<string, string>;
  const parsed = parseInt(slide, 10);
  const valid = !Number.isNaN(parsed) && parsed >= 1 && parsed <= totalSlides;
  const clamped = Number.isNaN(parsed) ? 1 : Math.max(1, Math.min(parsed, totalSlides));

  // Hooks run unconditionally; the invalid-param redirect happens as an effect
  // so hook order never changes between renders.
  useEffect(() => {
    if (!valid) {
      navigate({ to: "/deck/$slide", params: { slide: String(clamped) }, replace: true });
    }
  }, [valid, clamped, navigate]);

  const currentSlide = clamped;
  const reducedMotion = useReducedMotionInline();

  const isStatic =
    search?.static === "1" ||
    (typeof window !== "undefined" &&
      (window as unknown as Record<string, unknown>).__OVERWATCH_STATIC__ === true);

  const slideEntry = slideRegistry[currentSlide - 1];
  const transitionType: TransitionType =
    isStatic || reducedMotion
      ? "none"
      : slideEntry?.transition ?? config.transition;
  const transitionDuration =
    slideEntry?.transitionDuration ?? config.transitionDuration;

  const direction = currentSlide > prevSlideRef ? 1 : -1;
  const directionRef = useRef(direction);
  directionRef.current = direction;

  useMemo(() => {
    prevSlideRef = currentSlide;
  }, [currentSlide]);

  preloadSlide(currentSlide - 1);
  preloadSlide(currentSlide + 1);
  preloadSlide(currentSlide + 2);

  const variants = getTransitionVariants(
    transitionType,
    directionRef.current,
    transitionDuration,
  );

  if (!valid) return null;

  const SlideComponent = getSlideComponent(currentSlide);

  return (
    <DeckShell currentSlide={currentSlide} slides={slideList}>
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={currentSlide}
          initial={variants.initial}
          animate={variants.animate}
          exit={variants.exit}
          style={{ width: "100%", height: "100%" }}
        >
          <Suspense
            fallback={
              <div className="flex items-center justify-center h-full w-full">
                <div className="w-8 h-8 border-2 border-neutral-200 border-t-neutral-900 rounded-full animate-spin" />
              </div>
            }
          >
            <SlideComponent />
          </Suspense>
        </motion.div>
      </AnimatePresence>
    </DeckShell>
  );
}
