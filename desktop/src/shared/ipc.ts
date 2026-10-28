export const IPC = {
  licenseGet: "license:get",
  licenseSubmit: "license:submit",
  scanRun: "scan:run",
  scanCancel: "scan:cancel",
  scanProgress: "scan:progress",
  reportOpenPdf: "report:openPdf",
  reportOpenHtml: "report:openHtml",
  reportExportEvidence: "report:exportEvidence",
  appInfo: "app:info",
} as const;

export type Phase = "starting" | "host" | "backup" | "patch" | "software" | "protection" | "recovery" | "engine" | "done";
export type ScanProgress = { runId: string; phase: Phase; elapsedMs: number };