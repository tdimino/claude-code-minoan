import { lazy, type ComponentType } from "react";

/**
 * Deck configuration — customize title, auth, design, and slide registry here.
 */
export const config = {
  title: "My Presentation",

  auth: {
    /** Set to empty string to disable password protection */
    password: "",
  },

  design: {
    width: 1920,
    height: 1080,
    minViewportWidth: 375,
  },

  navigation: {
    /** Milliseconds before sidebar auto-collapses */
    autoCollapseDelay: 3000,
  },
} as const;

// ---------------------------------------------------------------------------
// Slide registry — add your slides here
// ---------------------------------------------------------------------------

export interface SlideEntry {
  id: string;
  fileKey: string;
  title: string;
  shortTitle: string;
}

export const slides: SlideEntry[] = [
  {
    id: "cover",
    fileKey: "01-cover",
    title: "Cover",
    shortTitle: "Cover",
  },
  // Add more slides:
  // { id: "problem", fileKey: "02-problem", title: "The Problem", shortTitle: "Problem" },
];

export const totalSlides = slides.length;

// ---------------------------------------------------------------------------
// Lazy component loader
// ---------------------------------------------------------------------------

const slideModules: Record<string, () => Promise<{ default: ComponentType }>> =
  {
    "01-cover": () => import("./slides/01-cover"),
    // Add more:
    // "02-problem": () => import("./slides/02-problem"),
  };

// Pre-build lazy wrappers at module load time (not during render)
const lazySlides: Record<string, ComponentType> = Object.fromEntries(
  Object.entries(slideModules).map(([key, loader]) => [key, lazy(loader)])
);

const NullComponent = () => null;

export function getSlideComponent(slideNumber: number): ComponentType {
  const index = slideNumber - 1;
  if (index < 0 || index >= slides.length) return NullComponent;
  return lazySlides[slides[index].fileKey] ?? NullComponent;
}

/** Preload a slide by number (call for adjacent slides) */
export function preloadSlide(slideNumber: number): void {
  const index = slideNumber - 1;
  if (index < 0 || index >= slides.length) return;
  const fileKey = slides[index].fileKey;
  slideModules[fileKey]?.();
}

/** Navigation-ready slide list with numbers */
export const slideList = slides.map((s, i) => ({
  number: i + 1,
  title: s.title,
  shortTitle: s.shortTitle,
}));
