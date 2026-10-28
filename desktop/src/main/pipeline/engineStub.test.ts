// @vitest-environment node
// desktop/src/main/pipeline/engineStub.test.ts
// Regression: the AG_STUB=1 engine stub must accept exactly the argv that
// runEngine builds for the real engine (--in/--out/--baseline/--run-id/--org).
// A PowerShell param() block cannot bind "--run-id", which made every stubbed
// scan end on the "Analysis failed" screen.
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const repoRoot = path.resolve(__dirname, "..", "..", "..", "..");
const stubDir = path.join(repoRoot, "installer", "stubs");
const powershell = path.join(
  process.env.SystemRoot ?? "C:\\Windows",
  "System32", "WindowsPowerShell", "v1.0", "powershell.exe"
);

vi.mock("../paths", () => ({
  paths: {
    engine: () => ({
      cmd: powershell,
      prefixArgs: [
        "-NoLogo", "-NoProfile", "-NonInteractive",
        "-ExecutionPolicy", "Bypass", "-File",
        path.join(stubDir, "engine-stub.ps1"),
      ],
      cwd: stubDir,
    }),
    baseline: () => path.join(repoRoot, "baseline", "software-baseline.json"),
  },
}));

import { runEngine } from "./runEngine";

describe.runIf(process.platform === "win32")("engine stub contract", () => {
  let runDir = "";

  beforeEach(async () => {
    runDir = await fs.mkdtemp(path.join(os.tmpdir(), "ag-engine-stub-"));
    await fs.copyFile(path.join(stubDir, "scan.stub.json"), path.join(runDir, "scan.json"));
  });

  afterEach(async () => {
    await fs.rm(runDir, { recursive: true, force: true });
  });

  it("accepts the runEngine argv and writes all report files", async () => {
    const res = await runEngine(
      runDir,
      "2026-10-28T04-59-59Z_2b23",
      "Acme Holdings (Pty) Ltd",
      new AbortController().signal
    );
    expect(res.stderr).toBe("");
    expect(res.code).toBe(0);
    expect(res.timedOut).toBe(false);

    const files = (await fs.readdir(runDir)).sort();
    expect(files).toEqual(
      ["action-plan.pdf", "evidence.json", "report.html", "report.json", "scan.json"]
    );
    const report = JSON.parse(await fs.readFile(path.join(runDir, "report.json"), "utf-8"));
    expect(typeof report).toBe("object");
  }, 20_000);
});
