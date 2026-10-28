/// <reference types="vite/client" />
import type { AppInfo, LicenseState, ScanProgress, ScanResult } from "../../shared/ipc";

interface AntigravityApi {
  getLicense: () => Promise<LicenseState>;
  submitLicense: (token: string) => Promise<LicenseState>;
  runScan: () => Promise<ScanResult>;
  cancelScan: () => Promise<void>;
  onProgress: (cb: (p: ScanProgress) => void) => () => void;
  openPdf: (runId: string) => Promise<{ ok: boolean }>;
  openHtml: (runId: string) => Promise<{ ok: boolean }>;
  exportEvidence: (runId: string) => Promise<{ ok: boolean; savedTo?: string }>;
  appInfo: () => Promise<AppInfo>;
}

declare global {
  interface Window {
    antigravity: AntigravityApi;
  }
}

export {};
