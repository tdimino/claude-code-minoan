import { useState, useEffect, type ReactNode } from "react";
import { useNavigate } from "@tanstack/react-router";
import { config } from "../../config";
import { Sidebar } from "../navigation/Sidebar";
import { SlideScaler } from "../navigation/SlideScaler";
import { SlideCounter } from "./SlideCounter";
import { PasswordGate } from "./PasswordGate";
import { MobileBlock } from "./MobileBlock";
import { useKeyboardNav } from "../navigation/KeyboardNav";

interface DeckShellProps {
  children: ReactNode;
  currentSlide: number;
  slides: Array<{ number: number; title: string; shortTitle: string }>;
}

function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // No password configured — skip auth
    if (!config.auth.password) {
      setIsAuthenticated(true);
      setIsLoading(false);
      return;
    }

    // Check URL param
    const params = new URLSearchParams(window.location.search);
    if (params.get("pw") === config.auth.password) {
      sessionStorage.setItem("deck-auth", "true");
      params.delete("pw");
      const clean = window.location.pathname + (params.toString() ? `?${params}` : "") + window.location.hash;
      window.history.replaceState({}, "", clean);
      setIsAuthenticated(true);
      setIsLoading(false);
      return;
    }

    // Check session
    setIsAuthenticated(sessionStorage.getItem("deck-auth") === "true");
    setIsLoading(false);
  }, []);

  const login = (password: string) => {
    if (password === config.auth.password) {
      sessionStorage.setItem("deck-auth", "true");
      setIsAuthenticated(true);
      return true;
    }
    return false;
  };

  return { isAuthenticated, isLoading, login };
}

function useMobileCheck() {
  const [isMobile, setIsMobile] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const check = () => {
      setIsMobile(window.innerWidth < config.design.minViewportWidth);
      setIsChecking(false);
    };
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  return { isMobile, isChecking };
}

export function DeckShell({ children, currentSlide, slides }: DeckShellProps) {
  const navigate = useNavigate();
  const auth = useAuth();
  const mobile = useMobileCheck();
  const total = slides.length;

  useKeyboardNav({
    currentSlide,
    totalSlides: total,
    disabled: !auth.isAuthenticated,
  });

  const handleNavigate = (n: number) => {
    if (n >= 1 && n <= total) {
      navigate({ to: "/deck/$slide", params: { slide: String(n) } });
    }
  };

  // Loading state
  if (auth.isLoading || mobile.isChecking) {
    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{ backgroundColor: "var(--color-bg-cream)" }}
      >
        <div
          className="text-[10px] uppercase tracking-[0.3em] animate-pulse"
          style={{ fontFamily: "var(--font-body)", color: "var(--color-text-muted)" }}
        >
          Loading presentation...
        </div>
      </div>
    );
  }

  if (mobile.isMobile) return <MobileBlock />;
  if (!auth.isAuthenticated) return <PasswordGate login={auth.login} />;

  return (
    <div className="fixed inset-0 z-50 flex" style={{ backgroundColor: "var(--color-bg-cream)" }}>
      <Sidebar slides={slides} currentSlide={currentSlide} onNavigate={handleNavigate} />
      <div className="flex-1 flex items-center justify-center overflow-hidden relative">
        <SlideScaler>{children}</SlideScaler>
        <SlideCounter current={currentSlide} total={total} />
      </div>
    </div>
  );
}
