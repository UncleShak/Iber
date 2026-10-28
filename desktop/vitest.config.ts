// desktop/vitest.config.ts
import { defineConfig } from "vitest/config";
import { resolve } from "path";

export default defineConfig({
  resolve: { alias: { "@": resolve(__dirname, "src/renderer/src") } },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
