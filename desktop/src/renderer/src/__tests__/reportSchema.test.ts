// desktop/src/renderer/src/__tests__/reportSchema.test.ts  (manual §4.14)
// Needs "resolveJsonModule": true in tsconfig.web.json for typecheck.
import { describe, it, expect } from "vitest";
import allStates from "../mocks/report.all-states.json";
import { reportSchema } from "../lib/reportSchema";

const clone = () => structuredClone(allStates) as any;

describe("reportSchema", () => {
  it("accepts the all-states mock", () => {
    const r = reportSchema.safeParse(allStates);
    expect(r.success).toBe(true);
  });

  it("rejects a report with a missing category", () => {
    const bad = clone();
    bad.categories.pop();
    expect(reportSchema.safeParse(bad).success).toBe(false);
  });

  it("rejects categories in the wrong order", () => {
    const bad = clone();
    [bad.categories[0], bad.categories[1]] = [bad.categories[1], bad.categories[0]];
    expect(reportSchema.safeParse(bad).success).toBe(false);
  });

  it("rejects more than 3 top fixes", () => {
    const bad = clone();
    bad.top_fixes = ["enable-defender", "update-outdated-apps", "install-updates", "enable-cfa"];
    expect(reportSchema.safeParse(bad).success).toBe(false);
  });

  it("rejects a top fix that does not exist", () => {
    const bad = clone();
    bad.top_fixes = ["does-not-exist"];
    expect(reportSchema.safeParse(bad).success).toBe(false);
  });

  it("rejects an unknown status", () => {
    const bad = clone();
    bad.categories[0].status = "purple";
    expect(reportSchema.safeParse(bad).success).toBe(false);
  });

  it("rejects a different major schema version", () => {
    const bad = clone();
    bad.schema_version = "2.0.0";
    expect(reportSchema.safeParse(bad).success).toBe(false);
  });
});
