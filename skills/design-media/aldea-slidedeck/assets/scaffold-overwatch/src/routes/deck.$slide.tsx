import { Suspense } from "react";
import { useParams } from "@tanstack/react-router";
import { getSlideComponent, preloadSlide, slideList } from "../config";
import { DeckShell } from "../components/chrome/DeckShell";

export function SlideRoute() {
  const { slide } = useParams({ strict: false }) as { slide: string };
  const currentSlide = parseInt(slide, 10);
  const SlideComponent = getSlideComponent(currentSlide);

  // Preload adjacent slides
  preloadSlide(currentSlide - 1);
  preloadSlide(currentSlide + 1);
  preloadSlide(currentSlide + 2);

  return (
    <DeckShell currentSlide={currentSlide} slides={slideList}>
      <Suspense
        fallback={
          <div className="flex items-center justify-center h-full w-full">
            <div className="w-8 h-8 border-2 border-neutral-200 border-t-neutral-900 rounded-full animate-spin" />
          </div>
        }
      >
        <SlideComponent />
      </Suspense>
    </DeckShell>
  );
}
