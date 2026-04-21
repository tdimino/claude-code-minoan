import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@wterm/shared": resolve(__dirname, "../src/protocol.ts"),
    },
  },
  server: {
    proxy: {
      "/api": "http://localhost:3036",
      "/ws": {
        target: "ws://localhost:3036",
        ws: true,
      },
    },
  },
});
