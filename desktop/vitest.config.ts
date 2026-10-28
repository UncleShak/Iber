// desktop/vitest.config.ts
import { defineConfig } from "vitest/config";
import { resolve } from "path";

export default defineConfig({
  resolve: { alias: { "@": resolve(__dirname, "src/renderer/src") } },
  esbuild: { jsx: "automatic" }, // so .tsx tests compile without relying on tsconfig lookup
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
