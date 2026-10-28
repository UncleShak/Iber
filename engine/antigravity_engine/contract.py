"""Typed mirror of shared/contract/scan.schema.json (s0.5, s0.6).

The JSON Schema is the source of truth and is validated first (parser.py);
these models give the scorers typed attribute access. A field with no
default is required (key must be present) even when its value may be null.
Unknown keys are ignored for forward compatibility (s0.6).
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict


class Status(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class _Model(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class Section(_Model):
    status: Status
    error: str | None


class Host(_Model):
    hostname_hash: str
    os_caption: str
    os_build: str
    os_edition: str
    is_admin: bool
    ps_version: str


class Backup(Section):
    file_history_enabled: bool | None
    file_history_last_backup: str | None
    windows_backup_last_success: str | None
    onedrive_kfm_folders: list[Literal["Desktop", "Documents", "Pictures"]]
    shadow_copy_count: int | None
    third_party_agents: list[str]


class Hotfix(_Model):
    kb: str
    installed_on: str


class Patch(Section):
    hotfix_count: int | None
    latest_hotfix_installed_on: str | None
    days_since_latest_hotfix: int | None
    hotfixes: list[Hotfix]
    pending_reboot: bool | None


class InstalledApp(_Model):
    name: str
    version: str
    publisher: str


class Software(Section):
    installed: list[InstalledApp]


class BitLocker(Section):
    os_volume_protection: Literal["on", "off"] | None
    os_volume_encryption_pct: int | None
    encryption_method: str | None = None


class Defender(Section):
    antivirus_enabled: bool | None
    realtime_enabled: bool | None
    tamper_protected: bool | None
    signature_age_days: int | None
    third_party_av: str | None = None


class Cfa(Section):
    mode: Literal["enabled", "disabled", "audit"] | None


class AsrRule(_Model):
    id: str
    action: Literal["block", "audit", "warn", "off"]


class Asr(Section):
    rules: list[AsrRule]


class Protection(_Model):
    bitlocker: BitLocker
    defender: Defender
    cfa: Cfa
    asr: Asr


class Recovery(Section):
    winre_enabled: bool | None
    system_restore_enabled: bool | None
    restore_point_count: int | None
    latest_restore_point: str | None


class ScanModel(_Model):
    schema_version: str
    run_id: str
    collected_at: str
    collector_version: str
    duration_ms: int
    host: Host
    backup: Backup
    patch: Patch
    software: Software
    protection: Protection
    recovery: Recovery
