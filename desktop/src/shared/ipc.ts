// IPC contract shared across main, preload, and renderer layers.
// Channel names and payload shapes are strictly pinned to prevent boundary drift.

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

export type LicenseState =
  | { status: "none" }
  | { status: "valid"; lic: string; org: string; exp: number }
  | {
      status: "invalid";
      reason:
        | "malformed"
        | "unknown_key"
        | "bad_signature"
        | "not_yet_valid"
        | "expired"
        | "not_entitled";
    };

export type Phase =
  | "starting"
  | "host"
  | "backup"
  | "patch"
  | "software"
  | "protection"
  | "recovery"
  | "engine"
  | "done";

export type ScanProgress = {
  runId: string;
  phase: Phase;
  elapsedMs: number;
};

export type ScanResult =
  | { ok: true; runId: string; report: unknown; pdfAvailable: boolean }
  | {
      ok: false;
      runId: string;
      stage: "license" | "collector" | "engine" | "cancelled" | "timeout";
      message: string;
    };

export type ExportEvidenceResult = {
  ok: boolean;
  savedTo?: "user-chosen";
};

export type AppInfo = {
  version: string;
  isAdmin: boolean;
  mock: boolean;
};
