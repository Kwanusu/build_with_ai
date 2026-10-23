import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    plugins: [react(), tailwindcss()],
    server: {
      // The API only accepts requests from this address and GitHub sends sign-ins back to it, so never
      // quietly move to another port: stop with an error instead.
      port: 5173,
      strictPort: true,
      // In development the page calls /api on its own address and Vite forwards it to the Flask server.
      proxy: { "/api": env.VITE_API_PROXY ?? "http://127.0.0.1:5000" },
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/test-setup.ts"],
      css: false,
      include: ["src/**/*.test.{ts,tsx}"],
    },
  };
});
