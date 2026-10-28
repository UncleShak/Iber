// desktop/src/main/ipc.ts
import { ipcMain, shell, dialog, app, BrowserWindow } from "electron";
import fs from "node:fs/promises";
import path from "node:path";
import { IPC, type ScanProgress } from "../shared/ipc";
import { paths } from "./paths";
import { validateRunId, prepareRunFolder } from "./runs";
import { runCollector } from "./pipeline/runCollector";
import { runEngine } from "./pipeline/runEngine";
import { runMockScan } from "./mock";
import { verifyLicense } from "./license/verify";

let currentAbort: AbortController | null = null;

const logErr = async (msg: string) => {
  try {
    await fs.mkdir(paths.logsRoot(), { recursive: true });
    await fs.writeFile(path.join(paths.logsRoot(), "last-error.txt"), msg, "utf-8");
  } catch {}
};

const getWin = () => BrowserWindow.getAllWindows()[0];

export function registerIpc() {
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

  ipcMain.handle(IPC.appInfo, () => ({ version: app.getVersion(), isAdmin: false, mock: paths.mockEnabled() }));

  ipcMain.handle(IPC.scanRun, async () => {
    if (currentAbort) return { ok: false, runId: "", stage: "collector", message: "A scan is already running." };
    let licenseOrg = "";
    try {
      const res = verifyLicense((await fs.readFile(paths.licenseFile(), "utf-8")).trim());
      if (!res.ok) return { ok: false, runId: "", stage: "license", message: "License is no longer valid." };
      licenseOrg = res.org;
    } catch { return { ok: false, runId: "", stage: "license", message: "No valid license found." }; }

    const now = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    const ts = `${now.getUTCFullYear()}-${pad(now.getUTCMonth()+1)}-${pad(now.getUTCDate())}T${pad(now.getUTCHours())}-${pad(now.getUTCMinutes())}-${pad(now.getUTCSeconds())}Z`;
    const runId = `${ts}_${Math.floor(Math.random()*65536).toString(16).padStart(4,"0")}`;
    
    currentAbort = new AbortController();
    const signal = currentAbort.signal;
    const start = Date.now();
    const progress = (phase: ScanProgress["phase"]) => getWin()?.webContents.send(IPC.scanProgress, { runId, phase, elapsedMs: Date.now() - start });

    try {
      if (paths.mockEnabled()) {
        const out = await runMockScan((phase, elapsedMs) => getWin()?.webContents.send(IPC.scanProgress, { runId, phase, elapsedMs }), signal);
        if (!out.ok) return { ok: false, runId, stage: out.stage, message: out.message };
        return { ok: true, runId: out.runId, report: out.report, pdfAvailable: out.pdfAvailable };
      }
      const runDir = await prepareRunFolder(runId);
      progress("starting");
      const cRes = await runCollector(runDir, runId, (line) => line.startsWith("AG-PHASE:") && progress(line.split(":")[1] as any), signal);
      if (signal.aborted) return { ok: false, runId, stage: "cancelled", message: "Scan cancelled." };
      if (cRes.code !== 0 || cRes.timedOut) {
        await logErr(`Collector failed: ${cRes.code} ${cRes.stderr}`);
        return { ok: false, runId, stage: "collector", message: "System check failed. Details saved to a log file." };
      }
      progress("engine");
      const eRes = await runEngine(runDir, runId, licenseOrg, signal);
      if (signal.aborted) return { ok: false, runId, stage: "cancelled", message: "Scan cancelled." };
      if (eRes.code !== 0 && eRes.code !== 2 && eRes.code !== 3 || eRes.timedOut) {
        await logErr(`Engine failed: ${eRes.code} ${eRes.stderr}`);
        return { ok: false, runId, stage: "engine", message: "Analysis failed. Details saved to a log file." };
      }
      const buf = await fs.readFile(path.join(runDir, "report.json"));
      if (buf.length > 2 * 1024 * 1024) throw new Error("Report too large");
      const report = JSON.parse(buf.toString("utf-8"));
      progress("done");
      return { ok: true, runId, report, pdfAvailable: eRes.code === 0 };
    } catch (err: any) {
      await logErr(`Scan error: ${err.message}`);
      return { ok: false, runId, stage: "engine", message: "Unexpected error. Details saved to a log file." };
    } finally { currentAbort = null; }
  });

  ipcMain.handle(IPC.scanCancel, () => { if (currentAbort) { currentAbort.abort(); currentAbort = null; } });

  const openFile = async (runId: string, file: string) => {
    if (!validateRunId(runId)) return { ok: false };
    try { await shell.openPath(path.join(paths.runsRoot(), runId, file)); return { ok: true }; } catch { return { ok: false }; }
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
