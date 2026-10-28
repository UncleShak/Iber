import { app, BrowserWindow, ipcMain } from 'electron';
import { join } from 'path';
import { IPC } from '../shared/ipc';

app.whenReady().then(() => {
  const win = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: true,
      contextIsolation: true,
      spellcheck: false
    }
  });
  
  win.setMenuBarVisibility(false);
  win.webContents.on('will-navigate', e => e.preventDefault());
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));

  if (process.env.ELECTRON_RENDERER_URL) {
    win.loadURL(process.env.ELECTRON_RENDERER_URL);
  } else {
    win.loadFile(join(__dirname, '../renderer/index.html'));
  }

  // --- MOCK BACKEND FOR DEMO ---
  ipcMain.handle(IPC.licenseGet, () => ({ status: 'none' }));
  ipcMain.handle(IPC.licenseSubmit, () => ({ status: 'valid', lic: 'AG-DEMO-0001', org: 'HackSecure Judges', exp: Date.now() + 86400000 }));
  ipcMain.handle(IPC.appInfo, () => ({ version: '1.0.0-demo', isAdmin: false, mock: true }));
  ipcMain.handle(IPC.reportOpenPdf, () => ({ ok: true }));
  ipcMain.handle(IPC.reportOpenHtml, () => ({ ok: true }));
  ipcMain.handle(IPC.reportExportEvidence, () => ({ ok: true, savedTo: "user-chosen" }));
  
  let cancel = false;
  ipcMain.handle(IPC.scanCancel, () => { cancel = true; });
  
  ipcMain.handle(IPC.scanRun, async () => {
    cancel = false;
    const phases: Array<{p: any, ms: number}> = [
      {p: "starting", ms: 1000}, {p: "host", ms: 1000}, {p: "backup", ms: 3000}, 
      {p: "patch", ms: 2000}, {p: "software", ms: 2000}, {p: "protection", ms: 4000}, 
      {p: "recovery", ms: 2000}, {p: "engine", ms: 1000}
    ];
    
    let elapsed = 0;
    for (const phase of phases) {
      if (cancel) return { ok: false, stage: "cancelled", message: "Scan cancelled by user." };
      win.webContents.send(IPC.scanProgress, { runId: "demo-run", phase: phase.p, elapsedMs: elapsed });
      await new Promise(r => setTimeout(r, phase.ms));
      elapsed += phase.ms;
    }
    win.webContents.send(IPC.scanProgress, { runId: "demo-run", phase: "done", elapsedMs: elapsed });
    
    return { ok: true, runId: "demo-run", pdfAvailable: true, report: mockReport };
  });
});

const mockReport = {
  schema_version: "1.0.0", run_id: "2026-11-14T17-02-44Z_beef", generated_at: "2026-11-14T17:02:46Z",
  engine_version: "0.1.0", baseline_version: "2026-11-01", evidence_id: "AG-7f3a9c2e41b0",
  overall: "red", summary: "2 urgent issues need attention this week. Some checks couldn't run.",
  categories: [
    { id: "backup", title: "Backup evidence", status: "green", explanation: "File History backed up this PC yesterday.", evidence: [{ label: "File History", value: "Last backup 13 Nov 2026", status: "green" }], fix_ids: [] },
    { id: "patch", title: "Windows updates", status: "amber", explanation: "A restart is waiting to finish updates.", evidence: [{ label: "Restart needed", value: "Yes", status: "amber" }], fix_ids: ["install-updates"] },
    { id: "software", title: "Outdated software", status: "red", explanation: "Google Chrome is out of date.", evidence: [{ label: "Google Chrome", value: "118.0.5993.118", status: "red" }], fix_ids: ["update-outdated-apps"] },
    { id: "protection", title: "Ransomware protections", status: "red", explanation: "Defender is switched off.", evidence: [{ label: "Defender antivirus", value: "Off", status: "red" }, { label: "BitLocker (C:)", value: "Not checked — needs admin", status: "unavailable" }], fix_ids: ["enable-defender"] },
    { id: "recovery", title: "Recovery readiness", status: "failed", explanation: "This check couldn't run on this PC.", evidence: [], fix_ids: [] }
  ],
  fixes: [
    { id: "enable-defender", category: "protection", severity: "red", title: "Turn Microsoft Defender back on", why: "Without antivirus, ransomware can run unnoticed.", steps: ["Open Start", "Turn on protection"], effort_minutes: 5, needs_admin: true },
    { id: "update-outdated-apps", category: "software", severity: "red", title: "Update Google Chrome", why: "Old browsers are a common way attackers get in.", steps: ["Open Chrome", "Update"], effort_minutes: 5, needs_admin: false },
    { id: "install-updates", category: "patch", severity: "amber", title: "Install Windows updates and restart", why: "Updates close security holes.", steps: ["Open Settings", "Restart"], effort_minutes: 30, needs_admin: true }
  ],
  top_fixes: ["enable-defender", "update-outdated-apps", "install-updates"],
  scan: { is_admin: false, duration_ms: 16000, os_caption: "Microsoft Windows 10 Pro" }
};