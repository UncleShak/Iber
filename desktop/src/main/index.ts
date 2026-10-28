// desktop/src/main/index.ts
// Single-window Electron shell. Security flags are non-negotiable (§4.4).
// The renderer never sees Node; the preload is the only bridge.
import { app, BrowserWindow, Menu, shell } from "electron";
import path from "node:path";
import { registerIpc } from "./ipc";

// One instance only — second launch focuses the existing window.
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) { app.quit(); }

let win: BrowserWindow | null = null;

function createWindow() {
  win = new BrowserWindow({
    width: 1280, height: 800, minWidth: 1024, minHeight: 640,
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      spellcheck: false,          // no dictionary downloads — PRV-11
      preload: path.join(__dirname, "../preload/index.js"),
    },
  });

  // Block navigation and new windows — the app is self-contained.
  win.webContents.on("will-navigate", (e) => e.preventDefault());
  win.webContents.setWindowOpenHandler(() => ({ action: "deny" }));

  // External links open in the default browser, never inside the app.
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  win.once("ready-to-show", () => win?.show());
  win.on("closed", () => { win = null; });

  // Dev: Vite dev server. Packaged: built HTML file.
  if (!app.isPackaged && process.env["ELECTRON_RENDERER_URL"]) {
    win.loadURL(process.env["ELECTRON_RENDERER_URL"]);
  } else {
    win.loadFile(path.join(__dirname, "../renderer/index.html"));
  }
}

app.whenReady().then(() => {
  // No menu in production — removes DevTools access for end users.
  if (app.isPackaged) Menu.setApplicationMenu(null);

  registerIpc();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("second-instance", () => {
  if (win) {
    if (win.isMinimized()) win.restore();
    win.focus();
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
