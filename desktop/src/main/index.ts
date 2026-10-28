// desktop/src/main/index.ts — INTERIM version until Schwan's real pipeline (§5) replaces the marked parts.
import { app, BrowserWindow, ipcMain, Menu } from "electron";
import { join } from "node:path";
import { IPC, type ScanResult } from "../shared/ipc";
import { isMockEnabled, runMockScan } from "./mock";

let win: BrowserWindow | null = null;
let activeScan: AbortController | null = null; // one scan at a time; one cancel token per run

function createWindow() {
  win = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      preload: join(__dirname, "../preload/index.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      spellcheck: false,
    },
  });

  win.webContents.on("will-navigate", (e) => e.preventDefault());
  win.webContents.setWindowOpenHandler(() => ({ action: "deny" }));

  if (app.isPackaged) Menu.setApplicationMenu(null);
  else win.setMenuBarVisibility(false);

  if (process.env.ELECTRON_RENDERER_URL) {
    win.loadURL(process.env.ELECTRON_RENDERER_URL);
    if (process.env.AG_DEVTOOLS === "1") win.webContents.openDevTools({ mode: "detach" });
  } else {
    win.loadFile(join(__dirname, "../renderer/index.html"));
  }
}

function registerIpc() {
  // --- SCHWAN/SHAKIR: replace with real licence verification (§3.11). This accepts ANY key. ---
  ipcMain.handle(IPC.licenseGet, () => ({ status: "none" }));
  ipcMain.handle(IPC.licenseSubmit, () => ({
    status: "valid",
    lic: "AG-DEMO-0001",
    org: "HackSecure Judges",
    exp: Date.now() + 86_400_000,
  }));

  ipcMain.handle(IPC.appInfo, () => ({ version: app.getVersion(), isAdmin: false, mock: isMockEnabled() }));

  // --- SCHWAN: real handlers open files by validated runId (§4.6 rules) / show the Save dialog ---
  ipcMain.handle(IPC.reportOpenPdf, () => ({ ok: true }));
  ipcMain.handle(IPC.reportOpenHtml, () => ({ ok: true }));
  ipcMain.handle(IPC.reportExportEvidence, () => ({ ok: true, savedTo: "user-chosen" }));

  ipcMain.handle(IPC.scanCancel, () => {
    activeScan?.abort();
  });

  ipcMain.handle(IPC.scanRun, async (): Promise<ScanResult> => {
    if (activeScan) {
      return { ok: false, runId: "", stage: "collector", message: "A scan is already running." };
    }

    // --- SCHWAN: replace this branch with runCollector -> runEngine (§4.7) and re-verify the licence first ---
    if (!isMockEnabled()) {
      return {
        ok: false,
        runId: "",
        stage: "collector",
        message: "The real scan isn't connected yet. Start the app with AG_MOCK=1 to use the demo scan.",
      };
    }

    activeScan = new AbortController();
    try {
      const out = await runMockScan(
        (phase, elapsedMs) => win?.webContents.send(IPC.scanProgress, { runId: "mock-run", phase, elapsedMs }),
        activeScan.signal
      );
      if (!out.ok) return { ok: false, runId: "", stage: out.stage, message: out.message };
      return { ok: true, runId: out.runId, report: out.report, pdfAvailable: out.pdfAvailable };
    } finally {
      activeScan = null;
    }
  });
}

app.whenReady().then(() => {
  registerIpc();
  createWindow();
});

app.on("window-all-closed", () => app.quit());
