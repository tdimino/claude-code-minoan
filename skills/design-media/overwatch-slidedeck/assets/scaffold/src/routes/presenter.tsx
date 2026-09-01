import { Suspense, useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "@tanstack/react-router";
import {
  slides as slideRegistry,
  totalSlides,
  getSlideComponent,
  preloadSlide,
} from "../config";
import { SlideScaler } from "../components/navigation/SlideScaler";

const CHANNEL_NAME = "overwatch-deck";

function useElapsedTimer() {
  const startRef = useRef(Date.now());
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const seconds = String(elapsed % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export function PresenterRoute() {
  const { slide } = useParams({ strict: false }) as { slide: string };
  const navigate = useNavigate();
  const parsed = parseInt(slide, 10);
  const currentSlide = Number.isNaN(parsed) ? 1 : Math.max(1, Math.min(parsed, totalSlides));
  const channelRef = useRef<BroadcastChannel | null>(null);

  const elapsed = useElapsedTimer();

  useEffect(() => {
    channelRef.current = new BroadcastChannel(CHANNEL_NAME);
    const handler = (e: MessageEvent) => {
      const slideNum = Number(e.data?.slide);
      if (slideNum >= 1 && slideNum <= totalSlides && slideNum !== currentSlide) {
        navigate({ to: "/presenter/$slide", params: { slide: String(slideNum) } });
      }
    };
    channelRef.current.addEventListener("message", handler);
    return () => {
      channelRef.current?.removeEventListener("message", handler);
      channelRef.current?.close();
    };
  }, [currentSlide, navigate]);

  const goToSlide = useCallback(
    (n: number) => {
      if (n >= 1 && n <= totalSlides) {
        navigate({ to: "/presenter/$slide", params: { slide: String(n) } });
        channelRef.current?.postMessage({ slide: n });
      }
    },
    [navigate],
  );

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " ") {
        e.preventDefault();
        if (currentSlide < totalSlides) goToSlide(currentSlide + 1);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        if (currentSlide > 1) goToSlide(currentSlide - 1);
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
  }, [currentSlide, goToSlide]);

  preloadSlide(currentSlide + 1);

  const CurrentComponent = getSlideComponent(currentSlide);
  const NextComponent =
    currentSlide < totalSlides ? getSlideComponent(currentSlide + 1) : null;
  const slideEntry = slideRegistry[currentSlide - 1];
  const notes = slideEntry?.notes ?? "";

  return (
    <div
      className="fixed inset-0 flex flex-col"
      style={{
        backgroundColor: "#1a1a1e",
        fontFamily: "var(--font-body)",
        color: "#e5e5e5",
      }}
    >
      <div className="flex items-center justify-between px-6 py-3 border-b border-white/10">
        <div className="flex items-center gap-4">
          <span
            className="text-xs tracking-[0.15em] uppercase font-medium"
            style={{ color: "var(--color-orange, #ff6e41)" }}
          >
            Presenter Mode
          </span>
          <span className="text-xs text-white/40">
            Slide {String(currentSlide).padStart(2, "0")}/{String(totalSlides).padStart(2, "0")}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span
            className="text-sm tabular-nums"
            style={{ fontFamily: "var(--font-mono)", color: "#a1a1aa" }}
          >
            {elapsed}
          </span>
        </div>
      </div>

      <div className="flex-1 flex min-h-0 p-4 gap-4">
        <div className="flex flex-col gap-4 flex-[3] min-w-0">
          <div className="flex-[3] min-h-0 flex items-center justify-center bg-black/30 rounded-lg overflow-hidden">
            <SlideScaler>
              <Suspense fallback={null}>
                <CurrentComponent />
              </Suspense>
            </SlideScaler>
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto bg-black/20 rounded-lg p-5">
            <div className="text-[10px] uppercase tracking-[0.2em] text-white/30 mb-3">
              Notes
            </div>
            {notes ? (
              <p
                className="text-sm leading-relaxed text-white/70 whitespace-pre-wrap"
                style={{ fontFamily: "var(--font-body)" }}
              >
                {notes}
              </p>
            ) : (
              <p className="text-sm text-white/20 italic">No notes for this slide.</p>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-4 flex-[1] min-w-0">
          <div className="flex-1 min-h-0 flex items-center justify-center bg-black/20 rounded-lg overflow-hidden">
            {NextComponent ? (
              <div className="w-full h-full flex items-center justify-center">
                <div className="text-[10px] uppercase tracking-[0.2em] text-white/30 absolute top-2 left-3 z-10">
                  Next
                </div>
                <SlideScaler>
                  <Suspense fallback={null}>
                    <NextComponent />
                  </Suspense>
                </SlideScaler>
              </div>
            ) : (
              <div className="text-sm text-white/20 italic">End of deck</div>
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => goToSlide(currentSlide - 1)}
              disabled={currentSlide <= 1}
              className="flex-1 py-2 rounded text-xs uppercase tracking-wider bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Prev
            </button>
            <button
              onClick={() => goToSlide(currentSlide + 1)}
              disabled={currentSlide >= totalSlides}
              className="flex-1 py-2 rounded text-xs uppercase tracking-wider bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              style={{ color: "var(--color-orange, #ff6e41)" }}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
