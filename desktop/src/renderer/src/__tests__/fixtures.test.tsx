// desktop/src/renderer/src/__tests__/fixtures.test.tsx  (manual §4.14, Appendix E: C2)
import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import ResultsScreen from "../screens/ResultsScreen";
import StatusBadge from "../components/StatusBadge";
import allStates from "../mocks/report.all-states.json";
import { reportSchema, STATUSES, type Report } from "../lib/reportSchema";

afterEach(cleanup);

const BADGE_TEXT = {
  red: "Act now",
  amber: "Improve",
  green: "Good",
  unavailable: "Not checked",
  failed: "Check failed",
} as const;

const BADGE_TOKEN = {
  red: "rag-red",
  amber: "rag-amber",
  green: "rag-green",
  unavailable: "rag-grey",
  failed: "rag-grey",
} as const;

const CARD_IDS = "#backup, #patch, #software, #protection, #recovery";

function renderResults(report: Report) {
  return render(
    <ResultsScreen report={report} runId="test-run" pdfAvailable={true} license={null} onScanAgain={() => {}} />
  );
}

// The hand-written all-states mock, plus every /shared/fixtures/report.*.json if the folder exists.
// (Repo layout: antigravity/shared/fixtures, antigravity/desktop/…; no matches is fine.)
const external = import.meta.glob("../../../../../shared/fixtures/report.*.json", {
  eager: true,
  import: "default",
}) as Record<string, unknown>;

const reports: Array<[string, unknown]> = [
  ["mocks/report.all-states.json", allStates],
  ...Object.entries(external),
];

describe("StatusBadge", () => {
  it.each(STATUSES)("draws icon + text + colour for %s", (status) => {
    const { container } = render(<StatusBadge status={status} />);
    const badge = screen.getByText(BADGE_TEXT[status]);
    expect(container.querySelector("svg")).not.toBeNull(); // icon
    expect(badge.className).toContain(BADGE_TOKEN[status]); // colour token, never a raw hex
    if (status === "failed") expect(badge.className).toContain("border-dashed");
  });
});

describe.each(reports)("ResultsScreen with %s", (_name, raw) => {
  const report = reportSchema.parse(raw);

  it("shows exactly 5 category cards", () => {
    const { container } = renderResults(report);
    expect(container.querySelectorAll(CARD_IDS).length).toBe(5);
  });

  it("shows the right badge text for every category and the overall status", () => {
    renderResults(report);
    for (const c of report.categories) {
      expect(screen.getAllByText(BADGE_TEXT[c.status]).length).toBeGreaterThan(0);
    }
    expect(screen.getAllByText(BADGE_TEXT[report.overall]).length).toBeGreaterThan(0);
  });

  it("shows at most 3 fixes, in top_fixes only", () => {
    renderResults(report);
    expect(report.top_fixes.length).toBeLessThanOrEqual(3);
    const top = new Set(report.top_fixes);
    for (const f of report.fixes) {
      const found = screen.queryAllByText(f.title, { exact: false }).length;
      if (top.has(f.id)) expect(found).toBeGreaterThan(0);
      else expect(found).toBe(0);
    }
  });
});

describe("all-states mock", () => {
  const report = reportSchema.parse(allStates);

  it('shows "Not checked" and "Check failed"', () => {
    renderResults(report);
    expect(screen.getAllByText(/Not checked/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Check failed").length).toBeGreaterThan(0);
  });

  it("does not double the \"Couldn't read:\" prefix", () => {
    renderResults(report);
    expect(screen.queryAllByText(/Couldn't read: Couldn't read:/).length).toBe(0);
    expect(screen.getAllByText(/Couldn't read:/).length).toBeGreaterThan(0);
  });

  it("notes when the scan ran without admin rights", () => {
    renderResults(report);
    expect(screen.getByText("Scanned without admin rights.")).toBeTruthy();
  });

  it("renders a hostile app name as plain text (RPT-07)", () => {
    const evil = structuredClone(report);
    evil.categories[2].evidence[0].label = "<script>alert(1)</script>";
    const { container } = renderResults(evil);
    expect(screen.getByText("<script>alert(1)</script>")).toBeTruthy();
    expect(container.querySelector("script")).toBeNull();
  });
});
