// Antigravity contract types — hand-written mirror of the JSON Schemas (manual Appendix A).
//   scan.schema.json     (A.1)  collector → engine
//   evidence.schema.json (A.3)  engine → relying party
// report.json types (A.2) belong to Brick A and are not defined here yet.
// Kept in step with the schemas by shared/contract/tests/ (test_contract.py drift check + types.check.ts).
// "Required" in §0.6 means the key is always present; the value may be null where the type allows.

/** ISO-8601 UTC, "YYYY-MM-DDTHH:MM:SSZ". */
export type IsoUtc = string;
/** Calendar date, "YYYY-MM-DD". */
export type IsoDate = string;

/** §0.9: set by the collector per section. */
export type SectionStatus = 'ok' | 'unavailable' | 'failed';
export type OneDriveFolder = 'Desktop' | 'Documents' | 'Pictures';
export type BitLockerProtection = 'on' | 'off';
export type CfaMode = 'enabled' | 'disabled' | 'audit';
export type AsrAction = 'block' | 'audit' | 'warn' | 'off';

export interface SectionBase {
  status: SectionStatus;
  /** Fixed text, max 200 chars, no paths (§3.4 rule 4). */
  error: string | null;
}

export interface ScanHost {
  /** "sha256:<hex>", salted — never the raw hostname. */
  hostname_hash: string;
  os_caption: string;
  /** Digits only, e.g. "22631". */
  os_build: string;
  /** EditionID; "Core" = Home. */
  os_edition: string;
  is_admin: boolean;
  ps_version: string;
}

export interface BackupSection extends SectionBase {
  file_history_enabled: boolean | null;
  file_history_last_backup: IsoUtc | null;
  windows_backup_last_success: IsoUtc | null;
  onedrive_kfm_folders: OneDriveFolder[];
  shadow_copy_count: number | null;
  third_party_agents: string[];
}

export interface Hotfix {
  /** "KB" + digits. */
  kb: string;
  installed_on: IsoDate;
}

export interface PatchSection extends SectionBase {
  hotfix_count: number | null;
  latest_hotfix_installed_on: IsoDate | null;
  days_since_latest_hotfix: number | null;
  /** Newest 10 only. */
  hotfixes: Hotfix[];
  pending_reboot: boolean | null;
}

export interface InstalledApp {
  name: string;
  version: string;
  publisher: string;
}

export interface SoftwareSection extends SectionBase {
  /** Max 500 entries. */
  installed: InstalledApp[];
}

export interface BitLockerSection extends SectionBase {
  os_volume_protection: BitLockerProtection | null;
  /** 0–100. */
  os_volume_encryption_pct: number | null;
  encryption_method?: string | null;
}

export interface DefenderSection extends SectionBase {
  antivirus_enabled: boolean | null;
  realtime_enabled: boolean | null;
  tamper_protected: boolean | null;
  signature_age_days: number | null;
  third_party_av?: string | null;
}

export interface CfaSection extends SectionBase {
  mode: CfaMode | null;
}

export interface AsrRule {
  /** Rule GUID, 36 chars. */
  id: string;
  action: AsrAction;
}

export interface AsrSection extends SectionBase {
  rules: AsrRule[];
}

export interface ProtectionBlock {
  bitlocker: BitLockerSection;
  defender: DefenderSection;
  cfa: CfaSection;
  asr: AsrSection;
}

export interface RecoverySection extends SectionBase {
  winre_enabled: boolean | null;
  system_restore_enabled: boolean | null;
  restore_point_count: number | null;
  latest_restore_point: IsoUtc | null;
}

/** scan.json — collector output, engine input (§0.5, A.1). */
export interface ScanJson {
  /** Semver; major must be 1. */
  schema_version: string;
  /** "YYYY-MM-DDTHH-MM-SSZ_xxxx"; also the run folder name. */
  run_id: string;
  collected_at: IsoUtc;
  collector_version: string;
  duration_ms: number;
  host: ScanHost;
  backup: BackupSection;
  patch: PatchSection;
  software: SoftwareSection;
  protection: ProtectionBlock;
  recovery: RecoverySection;
}

/** evidence.json — bundle a third party checks with `engine.exe --verify` (§2.14, A.3). */
export interface EvidenceBundle {
  evidence_version: string;
  run_id: string;
  created_at: IsoUtc;
  engine_version: string;
  baseline_version: string;
  /** "sha256:" + 64 hex. */
  baseline_sha256: string;
  /** scan.json embedded unchanged. */
  scan: ScanJson;
  /** report.json embedded unchanged; typed by Brick A (A.2). */
  report: Record<string, unknown>;
  scan_sha256: string;
  report_sha256: string;
  /** "AG-" + first 12 hex of report_sha256. */
  evidence_id: string;
}
