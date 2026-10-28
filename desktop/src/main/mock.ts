// desktop/src/main/mock.ts  (manual §4.12) — owner C
// AG_MOCK=1 replaces the collector + engine with a fake 10-second scan that returns a canned report.
// Licence checks still run for real. Dev only: ignored in packaged builds.
import { app } from "electron";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { Phase } from "../shared/ipc";

export function isMockEnabled(): boolean {
  return process.env.AG_MOCK === "1" && !app.isPackaged;
}

// ~10 s in total, phases in the order the real collector prints them (§4.8)
const TIMELINE: Array<[Exclude<Phase, "done">, number]> = [
  ["starting", 500],
  ["host", 500],
  ["backup", 2500],
  ["patch", 1500],
  ["software", 1500],
  ["protection", 2000],
  ["recovery", 1000],
  ["engine", 500],
];

export type MockOutcome =
  | { ok: true; runId: string; report: unknown; pdfAvailable: boolean }
  | { ok: false; stage: "cancelled" | "engine"; message: string };

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    if (signal.aborted) return resolve();
    const done = () => {
      clearTimeout(timer);
      signal.removeEventListener("abort", done);
      resolve();
    };
    const timer = setTimeout(done, ms);
    signal.addEventListener("abort", done, { once: true });
  });
}

/** AG_MOCK_FIXTURE=report.defender-off.json picks another fixture. Plain file names only. */
function loadReport(): unknown {
  const name = process.env.AG_MOCK_FIXTURE ?? "report.all-states.json";
  if (!/^[\w.-]+\.json$/.test(name)) throw new Error(`Bad AG_MOCK_FIXTURE name: ${name}`);
  const root = app.getAppPath(); // = desktop/ in dev
  const candidates = [
    join(root, "src", "renderer", "src", "mocks", name),
    join(root, "..", "shared", "fixtures", name),
  ];
  const found = candidates.find((p) => existsSync(p));
  if (!found) throw new Error(`Mock fixture not found: ${name}`);
  return JSON.parse(readFileSync(found, "utf8"));
}

export async function runMockScan(
  onProgress: (phase: Phase, elapsedMs: number) => void,
  signal: AbortSignal
): Promise<MockOutcome> {
  const start = Date.now();
  for (const [phase, ms] of TIMELINE) {
    if (signal.aborted) return { ok: false, stage: "cancelled", message: "Scan cancelled." };
    onProgress(phase, Date.now() - start);
    await sleep(ms, signal);
  }
  if (signal.aborted) return { ok: false, stage: "cancelled", message: "Scan cancelled." };

  let report: unknown;
  try {
    report = loadReport();
  } catch (e) {
    console.error(e);
    return { ok: false, stage: "engine", message: "The mock report couldn't be loaded." };
  }
  onProgress("done", Date.now() - start);
  const id = (report as { run_id?: unknown }).run_id;
  return { ok: true, runId: typeof id === "string" ? id : "mock-run", report, pdfAvailable: true };
}
