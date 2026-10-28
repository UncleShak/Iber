// desktop/src/preload/index.ts
import { contextBridge, ipcRenderer } from "electron";
import { IPC, type ScanProgress } from "../shared/ipc";

const api = {
  getLicense: () => ipcRenderer.invoke(IPC.licenseGet),
  submitLicense: (token: string) => ipcRenderer.invoke(IPC.licenseSubmit, token),
  runScan: () => ipcRenderer.invoke(IPC.scanRun),
  cancelScan: () => ipcRenderer.invoke(IPC.scanCancel),
  onProgress: (cb: (p: ScanProgress) => void) => {
    const handler = (_e: unknown, p: ScanProgress) => cb(p);
    ipcRenderer.on(IPC.scanProgress, handler);
    return () => {
      ipcRenderer.removeListener(IPC.scanProgress, handler);
    };
  },
  openPdf: (runId: string) => ipcRenderer.invoke(IPC.reportOpenPdf, runId),
  openHtml: (runId: string) => ipcRenderer.invoke(IPC.reportOpenHtml, runId),
  exportEvidence: (runId: string) =>
    ipcRenderer.invoke(IPC.reportExportEvidence, runId),
  appInfo: () => ipcRenderer.invoke(IPC.appInfo),
};

contextBridge.exposeInMainWorld("antigravity", api);

export type AntigravityApi = typeof api;
