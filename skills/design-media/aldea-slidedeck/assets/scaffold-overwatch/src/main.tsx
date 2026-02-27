import "./styles/globals.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import {
  createRouter,
  createRootRoute,
  createRoute,
  RouterProvider,
  redirect,
  Outlet,
} from "@tanstack/react-router";
import { SlideRoute } from "./routes/deck.$slide";
import { totalSlides } from "./config";

// Root route — just renders children
const rootRoute = createRootRoute({
  component: () => <Outlet />,
});

// Index route — redirect to first slide
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  beforeLoad: () => {
    if (totalSlides > 0) {
      throw redirect({ to: "/deck/$slide", params: { slide: "1" } });
    }
  },
  component: () => (
    <div className="h-screen flex items-center justify-center bg-neutral-900 text-white">
      <p className="text-sm text-neutral-400">
        No slides yet. Add slides to config.ts to get started.
      </p>
    </div>
  ),
});

// Deck layout route
const deckRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "deck",
  component: () => <Outlet />,
});

// Slide route
const slideRoute = createRoute({
  getParentRoute: () => deckRoute,
  path: "$slide",
  component: SlideRoute,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  deckRoute.addChildren([slideRoute]),
]);

const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
);
