// desktop/src/main/ipc.ts
import { ipcMain, shell, dialog, app, BrowserWindow } from "electron";
import fs from "node:fs/promises";
import path from "node:path";
import { IPC, type ScanProgress } from "../shared/ipc";
import { paths } from "./paths";
import { validateRunId, prepareRunFolder, generateRunId } from "./runs";
import { runCollector } from "./pipeline/runCollector";
import { runEngine } from "./pipeline/runEngine";
import { runProcess } from "./pipeline/runProcess";
import { runMockScan } from "./mock";
import { verifyLicense } from "./license/verify";
import { verifyPackagedResources } from "./integrity";

let currentAbort: AbortController | null = null;
let cachedIsAdmin: boolean | null = null;
let pendingAdminCheck: Promise<boolean> | null = null;

export async function detectIsAdmin(
  platform: NodeJS.Platform = process.platform
): Promise<boolean> {
  if (platform !== "win32") return false;
  const sysRoot = process.env.SystemRoot || "C:\\Windows";
  const netExe = path.win32.join(sysRoot, "System32", "net.exe");
  try {
    const res = await runProcess(netExe, ["session"], {
      cwd: sysRoot,
      timeoutMs: 3_000,
    });
    return res.code === 0 && !res.timedOut && !res.cancelled;
  } catch {
    return false;
  }
}

const logErr = async (msg: string) => {
  try {
    await fs.mkdir(paths.logsRoot(), { recursive: true });
    await fs.writeFile(path.join(paths.logsRoot(), "last-error.txt"), msg, "utf-8");
  } catch {}
};

// The Evidence ID is a hash of report.json, so it lives only in evidence.json (manual 2.14.1).
// Returns it for the Results footer, or undefined if the file is missing or not as expected.
const readEvidenceId = async (runDir: string): Promise<string | undefined> => {
  try {
    const buf = await fs.readFile(path.join(runDir, "evidence.json"));
    if (buf.length > 4 * 1024 * 1024) return undefined;
    const id = JSON.parse(buf.toString("utf-8"))?.evidence_id;
    return typeof id === "string" && /^AG-[0-9a-f]{12}$/.test(id) ? id : undefined;
  } catch {
    return undefined;
  }
};

const getWin = () => BrowserWindow.getAllWindows()[0];

export function registerIpc() {
  currentAbort = null;
  cachedIsAdmin = null;
  pendingAdminCheck = detectIsAdmin().then((val) => {
    cachedIsAdmin = val;
    return val;
  });

  ipcMain.handle(IPC.licenseGet, async () => {
    try {
      const token = (await fs.readFile(paths.licenseFile(), "utf-8")).trim();
      const res = verifyLicense(token);
      if (res.ok) {
        return { status: "valid", lic: res.lic, org: res.org, exp: res.exp };
      } else {
        const fail = res as { ok: false; reason: any };
        return { status: "invalid", reason: fail.reason };
      }
    } catch {
      return { status: "none" };
    }
  });

  ipcMain.handle(IPC.licenseSubmit, async (_, token: string) => {
    const res = verifyLicense(token.trim());
    if (res.ok) {
      await fs.mkdir(path.dirname(paths.licenseFile()), { recursive: true });
      await fs.writeFile(paths.licenseFile(), token.trim(), "utf-8");
      return { status: "valid", lic: res.lic, org: res.org, exp: res.exp };
    } else {
      const fail = res as { ok: false; reason: any };
      return { status: "invalid", reason: fail.reason };
    }
  });

  ipcMain.handle(IPC.appInfo, async () => {
    const isAdmin =
      cachedIsAdmin !== null
        ? cachedIsAdmin
        : await (pendingAdminCheck ?? detectIsAdmin());
    cachedIsAdmin = isAdmin;
    return { version: app.getVersion(), isAdmin, mock: paths.mockEnabled() };
  });

  ipcMain.handle(IPC.scanRun, async () => {
    if (currentAbort && !currentAbort.signal.aborted) {
      return { ok: false, runId: "", stage: "collector", message: "A scan is already running." };
    }
    let licenseOrg = "";
    try {
      const res = verifyLicense((await fs.readFile(paths.licenseFile(), "utf-8")).trim());
      if (!res.ok) return { ok: false, runId: "", stage: "license", message: "License is no longer valid." };
      licenseOrg = res.org;
    } catch { return { ok: false, runId: "", stage: "license", message: "No valid license found." }; }

    const runId = generateRunId();

    const mine = new AbortController();
    currentAbort = mine;
    const signal = mine.signal;
    const start = Date.now();
    const progress = (phase: ScanProgress["phase"]) => getWin()?.webContents.send(IPC.scanProgress, { runId, phase, elapsedMs: Date.now() - start });

    try {
      if (paths.mockEnabled()) {
        const out = await runMockScan((phase, elapsedMs) => getWin()?.webContents.send(IPC.scanProgress, { runId, phase, elapsedMs }), signal);
        if (!out.ok) return { ok: false, runId, stage: out.stage, message: out.message };
        const runDir = await prepareRunFolder(runId);
        await fs.writeFile(path.join(runDir, "report.json"), JSON.stringify(out.report, null, 2), "utf-8");
        return { ok: true, runId, report: out.report, pdfAvailable: false };
      }
      const integrity = verifyPackagedResources();
      if (!integrity.ok) {
        await logErr(`Integrity check failed: ${integrity.detail}`);
        return { ok: false, runId, stage: "collector", message: integrity.message };
      }
      const runDir = await prepareRunFolder(runId);
      progress("starting");
      const cRes = await runCollector(runDir, runId, (line) => line.startsWith("AG-PHASE:") && progress(line.split(":")[1] as any), signal);
      if (signal.aborted || cRes.cancelled) return { ok: false, runId, stage: "cancelled", message: "Scan cancelled." };
      if (cRes.code !== 0 || cRes.timedOut) {
        await logErr(`Collector failed: ${cRes.code} ${cRes.stderr}`);
        return { ok: false, runId, stage: "collector", message: "System check failed. Details saved to a log file." };
      }
      progress("engine");
      const eRes = await runEngine(runDir, runId, licenseOrg, signal);
      if (signal.aborted || eRes.cancelled) return { ok: false, runId, stage: "cancelled", message: "Scan cancelled." };
      if ((eRes.code !== 0 && eRes.code !== 2 && eRes.code !== 3) || eRes.timedOut) {
        await logErr(`Engine failed: ${eRes.code} ${eRes.stderr}`);
        return { ok: false, runId, stage: "engine", message: "Analysis failed. Details saved to a log file." };
      }
      const buf = await fs.readFile(path.join(runDir, "report.json"));
      if (buf.length > 2 * 1024 * 1024) throw new Error("Report too large");
      const report = JSON.parse(buf.toString("utf-8"));
      const evidenceId = await readEvidenceId(runDir);
      if (evidenceId) report.evidence_id = evidenceId;
      progress("done");
      return { ok: true, runId, report, pdfAvailable: eRes.code === 0 };
    } catch (err: any) {
      if (signal.aborted) return { ok: false, runId, stage: "cancelled", message: "Scan cancelled." };
      await logErr(`Scan error: ${err.message}`);
      return { ok: false, runId, stage: "engine", message: "Unexpected error. Details saved to a log file." };
    } finally {
      if (currentAbort === mine) currentAbort = null;
    }
  });

  ipcMain.handle(IPC.scanCancel, () => {
    currentAbort?.abort();
  });

  const openFile = async (runId: string, file: string) => {
    if (!validateRunId(runId)) return { ok: false };
    const target = path.join(paths.runsRoot(), runId, file);
    try {
      await fs.access(target);
      const err = await shell.openPath(target);
      if (err) return { ok: false };
      return { ok: true };
    } catch {
      return { ok: false };
    }
  };
  ipcMain.handle(IPC.reportOpenPdf, (_, id: string) => openFile(id, "action-plan.pdf"));
  ipcMain.handle(IPC.reportOpenHtml, (_, id: string) => openFile(id, "report.html"));

  ipcMain.handle(IPC.reportExportEvidence, async (_, runId: string) => {
    if (!validateRunId(runId)) return { ok: false };
    const src = path.join(paths.runsRoot(), runId, "evidence.json");
    try {
      await fs.access(src);
      const res = await dialog.showSaveDialog({ defaultPath: `evidence-${runId}.json`, filters: [{ name: "JSON", extensions: ["json"] }] });
      if (res.canceled || !res.filePath) return { ok: false };
      await fs.copyFile(src, res.filePath);
      return { ok: true, savedTo: "user-chosen" };
    } catch { return { ok: false }; }
  });
}
