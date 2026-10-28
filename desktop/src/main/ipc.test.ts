// @vitest-environment node
// desktop/src/main/ipc.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { IPC } from "../shared/ipc";

const {
  handlers,
  openExternalMock,
  openPathMock,
  showSaveDialogMock,
  sendProgressMock,
  runProcessMock,
  verifyLicenseMock,
  runMockScanMock,
  state,
} = vi.hoisted(() => ({
  handlers: new Map<string, (...args: any[]) => any>(),
  openExternalMock: vi.fn(),
  openPathMock: vi.fn(),
  showSaveDialogMock: vi.fn(),
  sendProgressMock: vi.fn(),
  runProcessMock: vi.fn(),
  verifyLicenseMock: vi.fn(),
  runMockScanMock: vi.fn(),
  state: { tempRoot: "" },
}));

vi.mock("electron", () => {
  class MockBrowserWindow {
    webContents = {
      on: vi.fn(),
      setWindowOpenHandler: vi.fn(),
      send: sendProgressMock,
    };
    once = vi.fn();
    on = vi.fn();
    loadURL = vi.fn();
    loadFile = vi.fn();
    show = vi.fn();
    focus = vi.fn();
    isMinimized = vi.fn(() => false);
    restore = vi.fn();
    static getAllWindows() {
      return [{ webContents: { send: sendProgressMock } }];
    }
  }

  return {
    app: {
      isPackaged: false,
      getVersion: () => "0.1.0",
      getAppPath: () => path.resolve(__dirname, "../.."),
      getPath: () => state.tempRoot || os.tmpdir(),
      setPath: vi.fn(),
      requestSingleInstanceLock: () => true,
      quit: vi.fn(),
      whenReady: () => new Promise(() => {}),
      on: vi.fn(),
    },
    BrowserWindow: MockBrowserWindow,
    Menu: { setApplicationMenu: vi.fn() },
    ipcMain: {
      handle: (channel: string, fn: (...args: any[]) => any) => {
        handlers.set(channel, fn);
      },
    },
    shell: {
      openExternal: (...args: any[]) => openExternalMock(...args),
      openPath: (...args: any[]) => openPathMock(...args),
    },
    dialog: {
      showSaveDialog: (...args: any[]) => showSaveDialogMock(...args),
    },
  };
});

vi.mock("./pipeline/runProcess", () => ({
  runProcess: (...args: any[]) => runProcessMock(...args),
}));

vi.mock("./license/verify", () => ({
  verifyLicense: (...args: any[]) => verifyLicenseMock(...args),
}));

vi.mock("./mock", () => ({
  runMockScan: (...args: any[]) => runMockScanMock(...args),
}));

import { registerIpc, detectIsAdmin } from "./ipc";
import { handleWindowOpen } from "./index";

const SAMPLE_REPORT = {
  schema_version: "1.0.0",
  run_id: "2026-10-28T03-11-22Z_0000",
  generated_at: "2026-10-28T03:11:22Z",
  engine_version: "0.1.0",
  baseline_version: "2026-10-27",
  overall: "amber",
  summary: "We couldn't read the scan results.",
  categories: [
    {
      id: "backup",
      title: "Backup evidence",
      status: "failed",
      explanation: "This check couldn't run because the scan results couldn't be read.",
      evidence: [],
      fix_ids: [],
    },
    {
      id: "patch",
      title: "Patch status",
      status: "failed",
      explanation: "This check couldn't run because the scan results couldn't be read.",
      evidence: [],
      fix_ids: [],
    },
    {
      id: "software",
      title: "Outdated software",
      status: "failed",
      explanation: "This check couldn't run because the scan results couldn't be read.",
      evidence: [],
      fix_ids: [],
    },
    {
      id: "protection",
      title: "Ransomware protections",
      status: "failed",
      explanation: "This check couldn't run because the scan results couldn't be read.",
      evidence: [],
      fix_ids: [],
    },
    {
      id: "recovery",
      title: "Recovery readiness",
      status: "failed",
      explanation: "This check couldn't run because the scan results couldn't be read.",
      evidence: [],
      fix_ids: [],
    },
  ],
  fixes: [],
  top_fixes: [],
  scan: {
    is_admin: false,
    duration_ms: 0,
    os_caption: "Unknown",
  },
};

describe("Brick D main-process & IPC tests", () => {
  const prevLocalAppData = process.env.LOCALAPPDATA;
  const prevMock = process.env.AG_MOCK;

  beforeEach(async () => {
    handlers.clear();
    vi.resetAllMocks();
    state.tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), "ag-ipc-test-"));
    process.env.LOCALAPPDATA = state.tempRoot;
    delete process.env.AG_MOCK;

    await fs.writeFile(path.join(state.tempRoot, "license.txt"), "AG1.valid.token", "utf-8");
    verifyLicenseMock.mockReturnValue({
      ok: true,
      lic: "AG-DEMO-0001",
      org: "Demo Org",
      exp: Math.floor(Date.now() / 1000) + 86400,
    });
  });

  afterEach(async () => {
    if (prevLocalAppData === undefined) delete process.env.LOCALAPPDATA;
    else process.env.LOCALAPPDATA = prevLocalAppData;

    if (prevMock === undefined) delete process.env.AG_MOCK;
    else process.env.AG_MOCK = prevMock;

    if (state.tempRoot) {
      await fs.rm(state.tempRoot, { recursive: true, force: true }).catch(() => {});
    }
  });

  describe("window-open handler (index.ts)", () => {
    it("opens https: URLs externally and denies http:, file: and javascript:", () => {
      expect(handleWindowOpen({ url: "https://example.com/help" })).toEqual({ action: "deny" });
      expect(openExternalMock).toHaveBeenCalledTimes(1);
      expect(openExternalMock).toHaveBeenCalledWith("https://example.com/help");

      openExternalMock.mockClear();
      expect(handleWindowOpen({ url: "http://example.com" })).toEqual({ action: "deny" });
      expect(handleWindowOpen({ url: "file:///C:/Windows/System32/cmd.exe" })).toEqual({ action: "deny" });
      expect(handleWindowOpen({ url: "javascript:alert(1)" })).toEqual({ action: "deny" });
      expect(handleWindowOpen({ url: "not a valid url" })).toEqual({ action: "deny" });
      expect(openExternalMock).not.toHaveBeenCalled();
    });
  });

  describe("isAdmin detection (detectIsAdmin & app:info)", () => {
    it("returns false off Windows without spawning net.exe", async () => {
      const resDarwin = await detectIsAdmin("darwin");
      const resLinux = await detectIsAdmin("linux");
      expect(resDarwin).toBe(false);
      expect(resLinux).toBe(false);
      expect(runProcessMock).not.toHaveBeenCalled();
    });

    it("returns false on Windows when net session exits non-zero or errors", async () => {
      runProcessMock.mockResolvedValueOnce({
        code: 2,
        timedOut: false,
        cancelled: false,
        stderr: "System error 5 has occurred. Access is denied.",
      });
      expect(await detectIsAdmin("win32")).toBe(false);
      expect(runProcessMock).toHaveBeenCalledWith(
        expect.stringMatching(/System32\\net\.exe$/i),
        ["session"],
        expect.objectContaining({ timeoutMs: 3_000 })
      );

      runProcessMock.mockRejectedValueOnce(new Error("spawn error"));
      expect(await detectIsAdmin("win32")).toBe(false);
    });

    it("returns true on Windows when net session exits 0 and caches the result in app:info", async () => {
      runProcessMock.mockResolvedValueOnce({
        code: 0,
        timedOut: false,
        cancelled: false,
        stderr: "",
      });
      expect(await detectIsAdmin("win32")).toBe(true);

      runProcessMock.mockClear();
      runProcessMock.mockResolvedValue({
        code: 2,
        timedOut: false,
        cancelled: false,
        stderr: "Access is denied.",
      });
      registerIpc();
      const appInfoHandler = handlers.get(IPC.appInfo)!;
      const info1 = await appInfoHandler();
      const info2 = await appInfoHandler();
      expect(info1.isAdmin).toBe(false);
      expect(info2.isAdmin).toBe(false);
      if (process.platform === "win32") {
        expect(runProcessMock).toHaveBeenCalledTimes(1);
      }
    });
  });

  describe("cancel race (scan:run / scan:cancel)", () => {
    it("allows an immediate second scan:run after cancel, and first scan's finally does not clear second scan's controller", async () => {
      runProcessMock.mockResolvedValueOnce({ code: 2, timedOut: false, cancelled: false, stderr: "" });
      registerIpc();

      const scanRun = handlers.get(IPC.scanRun)!;
      const scanCancel = handlers.get(IPC.scanCancel)!;

      let resolveFirstCollector!: (v: any) => void;
      let firstStarted!: () => void;
      const firstStartedPromise = new Promise<void>((r) => { firstStarted = r; });

      let secondSignal!: AbortSignal;
      let resolveSecondCollector!: (v: any) => void;
      let secondStarted!: () => void;
      const secondStartedPromise = new Promise<void>((r) => { secondStarted = r; });

      // Call 1: First scan's collector (hangs until we resolve it after second scan starts)
      runProcessMock.mockImplementationOnce((_cmd: string, _args: string[], _opts: any) => {
        firstStarted();
        return new Promise((resolve) => {
          resolveFirstCollector = resolve;
        });
      });

      // Call 2: Second scan's collector
      runProcessMock.mockImplementationOnce((_cmd: string, _args: string[], opts: any) => {
        secondSignal = opts.signal;
        const runDir = opts.cwd;
        secondStarted();
        return new Promise((resolve) => {
          resolveSecondCollector = async (res: any) => {
            await fs.writeFile(path.join(runDir, "report.json"), JSON.stringify(SAMPLE_REPORT), "utf-8");
            resolve(res);
          };
        });
      });

      // Call 3: Second scan's engine
      runProcessMock.mockResolvedValueOnce({
        code: 0,
        timedOut: false,
        cancelled: false,
        stderr: "",
      });

      // Start Scan 1
      const scan1Promise = scanRun();
      await firstStartedPromise;

      // Cancel Scan 1
      scanCancel();

      // Immediately start Scan 2 BEFORE Scan 1's collector promise resolves
      const scan2Promise = scanRun();
      await secondStartedPromise;
      expect(secondSignal.aborted).toBe(false);

      // Now let Scan 1 finish so its finally block runs while Scan 2 is in flight
      resolveFirstCollector({ code: 1, timedOut: false, cancelled: true, stderr: "" });
      const res1 = await scan1Promise;
      expect(res1).toEqual(expect.objectContaining({ ok: false, stage: "cancelled" }));

      // Verify Scan 1's finally did NOT clear Scan 2's controller:
      // calling scanCancel now must still abort Scan 2's signal
      scanCancel();
      expect(secondSignal.aborted).toBe(true);

      await resolveSecondCollector({ code: 1, timedOut: false, cancelled: true, stderr: "" });
      const res2 = await scan2Promise;
      expect(res2).toEqual(expect.objectContaining({ ok: false, stage: "cancelled" }));
    });
  });

  describe("engine exit codes", () => {
    const runWithEngineResult = async (engineOut: {
      code: number | null;
      timedOut: boolean;
      cancelled: boolean;
      stderr: string;
    }) => {
      runProcessMock.mockResolvedValueOnce({ code: 2, timedOut: false, cancelled: false, stderr: "" });
      registerIpc();
      const scanRun = handlers.get(IPC.scanRun)!;

      runProcessMock.mockImplementationOnce(async (_cmd: string, _args: string[], opts: any) => {
        await fs.writeFile(path.join(opts.cwd, "report.json"), JSON.stringify(SAMPLE_REPORT), "utf-8");
        return { code: 0, timedOut: false, cancelled: false, stderr: "" };
      });

      runProcessMock.mockResolvedValueOnce(engineOut);
      return scanRun();
    };

    it("engine exit 0 gives pdfAvailable:true; exits 2 and 3 give false; exit 1 and timeouts give stage:'engine'", async () => {
      const res0 = await runWithEngineResult({ code: 0, timedOut: false, cancelled: false, stderr: "" });
      expect(res0).toEqual(expect.objectContaining({ ok: true, pdfAvailable: true }));

      const res2 = await runWithEngineResult({ code: 2, timedOut: false, cancelled: false, stderr: "invalid input" });
      expect(res2).toEqual(expect.objectContaining({ ok: true, pdfAvailable: false }));

      const res3 = await runWithEngineResult({ code: 3, timedOut: false, cancelled: false, stderr: "pdf render error" });
      expect(res3).toEqual(expect.objectContaining({ ok: true, pdfAvailable: false }));

      const res1 = await runWithEngineResult({ code: 1, timedOut: false, cancelled: false, stderr: "crash" });
      expect(res1).toEqual(expect.objectContaining({ ok: false, stage: "engine" }));

      const resTimeout = await runWithEngineResult({ code: 0, timedOut: true, cancelled: false, stderr: "" });
      expect(resTimeout).toEqual(expect.objectContaining({ ok: false, stage: "engine" }));
    });

    // evidence: file contents for <run>/evidence.json, or null for no file
    const runWithEvidence = async (evidence: string | null) => {
      runProcessMock.mockResolvedValueOnce({ code: 2, timedOut: false, cancelled: false, stderr: "" });
      registerIpc();
      const scanRun = handlers.get(IPC.scanRun)!;

      runProcessMock.mockImplementationOnce(async (_cmd: string, _args: string[], opts: any) => {
        await fs.writeFile(path.join(opts.cwd, "report.json"), JSON.stringify(SAMPLE_REPORT), "utf-8");
        if (evidence !== null) await fs.writeFile(path.join(opts.cwd, "evidence.json"), evidence, "utf-8");
        return { code: 0, timedOut: false, cancelled: false, stderr: "" };
      });

      runProcessMock.mockResolvedValueOnce({ code: 0, timedOut: false, cancelled: false, stderr: "" });
      return scanRun();
    };

    it("puts evidence_id from evidence.json on the report so the Results footer can show it", async () => {
      const res = await runWithEvidence(JSON.stringify({ evidence_id: "AG-0123456789ab" }));
      expect(res).toEqual(expect.objectContaining({ ok: true }));
      expect(res.report.evidence_id).toBe("AG-0123456789ab");

      const modPath = "../renderer/src/lib/reportSchema";
      const { reportSchema } = await import(/* @vite-ignore */ modPath);
      const parsed = reportSchema.safeParse(res.report);
      expect(parsed.success).toBe(true);
      expect(parsed.data.evidence_id).toBe("AG-0123456789ab");
    });

    it("leaves evidence_id unset when evidence.json is missing, not JSON, or has a malformed ID", async () => {
      for (const evidence of [null, "{not json", JSON.stringify({ evidence_id: "AG-<b>x</b>" }), JSON.stringify({ evidence_id: 42 })]) {
        const res = await runWithEvidence(evidence);
        expect(res).toEqual(expect.objectContaining({ ok: true }));
        expect(res.report.evidence_id).toBeUndefined();
      }
    });

    it("renderer reportSchema accepts the engine's exit-2 error report", async () => {
      const modPath = "../renderer/src/lib/reportSchema";
      const { reportSchema } = await import(/* @vite-ignore */ modPath);
      expect(reportSchema.safeParse(SAMPLE_REPORT).success).toBe(true);
    });
  });

  describe("mock run ID & missing file open/export handlers", () => {
    it("uses generated runId in mock mode, writes report.json, sets pdfAvailable:false, and open/export return { ok:false } for missing files", async () => {
      process.env.AG_MOCK = "1";
      runProcessMock.mockResolvedValueOnce({ code: 2, timedOut: false, cancelled: false, stderr: "" });
      registerIpc();

      runMockScanMock.mockResolvedValueOnce({
        ok: true,
        runId: "report-all-states",
        report: SAMPLE_REPORT,
        pdfAvailable: true,
      });

      const scanRun = handlers.get(IPC.scanRun)!;
      const res = await scanRun();

      expect(res.ok).toBe(true);
      expect(res.runId).not.toBe("report-all-states");
      expect(res.runId).toMatch(/^[0-9TZ:-]+_[0-9a-f]{4}$/);
      expect(res.pdfAvailable).toBe(false);

      const writtenReport = JSON.parse(
        await fs.readFile(path.join(state.tempRoot, "Antigravity", "runs", res.runId, "report.json"), "utf-8")
      );
      expect(writtenReport.run_id).toBe(SAMPLE_REPORT.run_id);

      const openPdf = handlers.get(IPC.reportOpenPdf)!;
      const openHtml = handlers.get(IPC.reportOpenHtml)!;
      const exportEvidence = handlers.get(IPC.reportExportEvidence)!;

      expect(await openPdf({}, res.runId)).toEqual({ ok: false });
      expect(await openHtml({}, res.runId)).toEqual({ ok: false });
      expect(await exportEvidence({}, res.runId)).toEqual({ ok: false });
    });
  });
});
