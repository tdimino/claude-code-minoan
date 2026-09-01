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
import { PresenterRoute } from "./routes/presenter";
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

// Presenter layout route
const presenterLayout = createRoute({
  getParentRoute: () => rootRoute,
  path: "presenter",
  component: () => <Outlet />,
});

const presenterSlideRoute = createRoute({
  getParentRoute: () => presenterLayout,
  path: "$slide",
  component: PresenterRoute,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  deckRoute.addChildren([slideRoute]),
  presenterLayout.addChildren([presenterSlideRoute]),
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
