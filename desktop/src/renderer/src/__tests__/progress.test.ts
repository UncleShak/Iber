// desktop/src/renderer/src/__tests__/progress.test.ts  (manual §4.14)
import { describe, it, expect } from "vitest";
import { BANDS, PHASE_ORDER, progressPct } from "../lib/progress";

describe("progressPct", () => {
  it("stays inside each band (never reaches the band end)", () => {
    for (const phase of PHASE_ORDER) {
      const [s, e] = BANDS[phase];
      for (const t of [0, 100, 1000, 5000, 60_000, 10_000_000]) {
        const p = progressPct(phase, t);
        expect(p).toBeGreaterThanOrEqual(s);
        expect(p).toBeLessThanOrEqual(e - 1);
      }
    }
  });

  it("never decreases within a phase", () => {
    for (const phase of PHASE_ORDER) {
      let prev = -1;
      for (let t = 0; t <= 20_000; t += 250) {
        const p = progressPct(phase, t);
        expect(p).toBeGreaterThanOrEqual(prev);
        prev = p;
      }
    }
  });

  it("never decreases across the whole phase sequence, even when a phase is slow", () => {
    let prev = -1;
    for (const phase of PHASE_ORDER) {
      for (const t of [0, 500, 3000, 60_000]) {
        const p = progressPct(phase, t);
        expect(p).toBeGreaterThanOrEqual(prev);
        prev = p;
      }
    }
  });

  it("never shows 100 before done", () => {
    for (const phase of PHASE_ORDER) {
      expect(progressPct(phase, 10_000_000)).toBeLessThan(100);
    }
    expect(progressPct("done", 0)).toBe(100);
  });
});
