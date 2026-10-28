// Compile-time contract check for shared/contract/types.ts (Appendix A.1, A.3).
// Not run, only type-checked:
//   # cwd: antigravity
//   desktop\node_modules\.bin\tsc -p shared\contract\tests\tsconfig.json
// Valid objects must compile; every @ts-expect-error line must fail to compile.

import type {
  BitLockerSection,
  DefenderSection,
  EvidenceBundle,
  RecoverySection,
  ScanJson,
  SectionStatus,
} from '../types';

// ---- valid: §0.7 fixture 1, typed ----
export const healthy: ScanJson = {
  schema_version: '1.0.0',
  run_id: '2026-11-14T16-42-07Z_0001',
  collected_at: '2026-11-14T16:42:07Z',
  collector_version: '0.1.0',
  duration_ms: 8420,
  host: {
    hostname_hash: 'sha256:1111',
    os_caption: 'Microsoft Windows 11 Pro',
    os_build: '22631',
    os_edition: 'Professional',
    is_admin: true,
    ps_version: '5.1.22621.4391',
  },
  backup: {
    status: 'ok',
    error: null,
    file_history_enabled: true,
    file_history_last_backup: '2026-11-13T22:00:00Z',
    windows_backup_last_success: null,
    onedrive_kfm_folders: ['Desktop', 'Documents', 'Pictures'],
    shadow_copy_count: 3,
    third_party_agents: [],
  },
  patch: {
    status: 'ok',
    error: null,
    hotfix_count: 14,
    latest_hotfix_installed_on: '2026-11-05',
    days_since_latest_hotfix: 9,
    hotfixes: [{ kb: 'KB5044285', installed_on: '2026-11-05' }],
    pending_reboot: false,
  },
  software: {
    status: 'ok',
    error: null,
    installed: [{ name: 'Google Chrome', version: '131.0.6778.86', publisher: 'Google LLC' }],
  },
  protection: {
    bitlocker: {
      status: 'ok',
      error: null,
      os_volume_protection: 'on',
      os_volume_encryption_pct: 100,
      encryption_method: 'XtsAes128',
    },
    defender: {
      status: 'ok',
      error: null,
      antivirus_enabled: true,
      realtime_enabled: true,
      tamper_protected: true,
      signature_age_days: 0,
      third_party_av: null,
    },
    cfa: { status: 'ok', error: null, mode: 'enabled' },
    asr: { status: 'ok', error: null, rules: [{ id: 'd4f940ab-401b-4efc-aadc-ad5f3c50688a', action: 'block' }] },
  },
  recovery: {
    status: 'ok',
    error: null,
    winre_enabled: true,
    system_restore_enabled: true,
    restore_point_count: 2,
    latest_restore_point: '2026-11-10T09:12:00Z',
  },
};

// ---- valid: optional fields (⬜ in §0.6) may be omitted ----
export const blNoMethod: BitLockerSection = {
  status: 'unavailable',
  error: 'Requires administrator rights',
  os_volume_protection: null,
  os_volume_encryption_pct: null,
};
export const defNoThirdParty: DefenderSection = {
  status: 'ok',
  error: null,
  antivirus_enabled: false,
  realtime_enabled: false,
  tamper_protected: false,
  signature_age_days: 21,
};

// ---- valid: evidence bundle (A.3) ----
export const bundle: EvidenceBundle = {
  evidence_version: '1.0.0',
  run_id: healthy.run_id,
  created_at: '2026-11-14T16:42:09Z',
  engine_version: '0.1.0',
  baseline_version: '2026-11-01',
  baseline_sha256: 'sha256:aa',
  scan: healthy,
  report: { schema_version: '1.0.0' },
  scan_sha256: 'sha256:bb',
  report_sha256: 'sha256:cc',
  evidence_id: 'AG-7f3a9c2e41b0',
};

export const statuses: SectionStatus[] = ['ok', 'unavailable', 'failed'];

// ---- invalid: each must be a compile error ----

// @ts-expect-error status is ok | unavailable | failed (§0.9)
export const badStatus: SectionStatus = 'error';

// @ts-expect-error os_volume_protection is 'on' | 'off' | null
export const badProtection: BitLockerSection['os_volume_protection'] = 'yes';

// @ts-expect-error cfa mode is enabled | disabled | audit | null
export const badCfa: ScanJson['protection']['cfa']['mode'] = 'on';

// @ts-expect-error ASR action is block | audit | warn | off
export const badAsr: ScanJson['protection']['asr']['rules'][number]['action'] = 'enabled';

// @ts-expect-error OneDrive KFM folders are Desktop | Documents | Pictures only
export const badKfm: ScanJson['backup']['onedrive_kfm_folders'] = ['Downloads'];

// @ts-expect-error required-but-nullable key may not be omitted (§0.6 "Required" = key present)
export const missingKey: RecoverySection = {
  status: 'ok',
  error: null,
  winre_enabled: true,
  system_restore_enabled: true,
  restore_point_count: 2,
};

// @ts-expect-error is_admin is boolean, not string
export const badAdmin: ScanJson['host']['is_admin'] = 'yes';
