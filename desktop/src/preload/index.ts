import { contextBridge, ipcRenderer } from 'electron';
import { IPC } from '../shared/ipc';

contextBridge.exposeInMainWorld('antigravity', {
  getLicense: () => ipcRenderer.invoke(IPC.licenseGet),
  submitLicense: (t: string) => ipcRenderer.invoke(IPC.licenseSubmit, t),
  runScan: () => ipcRenderer.invoke(IPC.scanRun),
  cancelScan: () => ipcRenderer.invoke(IPC.scanCancel),
  onProgress: (cb: any) => {
    const h = (_: any, p: any) => cb(p);
    ipcRenderer.on(IPC.scanProgress, h);
    return () => ipcRenderer.removeListener(IPC.scanProgress, h);
  },
  openPdf: (id: string) => ipcRenderer.invoke(IPC.reportOpenPdf, id),
  openHtml: (id: string) => ipcRenderer.invoke(IPC.reportOpenHtml, id),
  exportEvidence: (id: string) => ipcRenderer.invoke(IPC.reportExportEvidence, id),
  appInfo: () => ipcRenderer.invoke(IPC.appInfo),
});