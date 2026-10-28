# Software baseline (manual s2.8)

- `software-baseline.json` - curated watch list the engine scores `software.installed[]` against (s2.5.3), plus the OS build floor (s2.5.2) and recommended ASR rules (s2.5.4).
- `software-baseline.schema.json` - JSON Schema (draft 2020-12); `antigravity_engine.baseline.load_baseline` validates against it on every load.

Versions are researched by hand from each vendor's page. The shipped product never looks anything up live.
When you change a version, also bump `baseline_version` and `checked_on`.

## TODO(Tshedi): verify each min_safe_version against source_url before 16:00 Day 1

Values below were filled from memory on 2026-10-27 and may be stale. Use the version that fixes the latest
security issue (not simply the newest release), and tick each line once checked.

- [ ] chrome (Google Chrome) - 142.0.7444.175 - https://chromereleases.googleblog.com/
- [ ] edge (Microsoft Edge) - 142.0.3595.90 - https://learn.microsoft.com/en-us/deployedge/microsoft-edge-relnotes-security
- [ ] firefox (Mozilla Firefox) - 145.0 - https://www.mozilla.org/en-US/security/known-vulnerabilities/firefox/ (ESR is deliberately not matched)
- [ ] acrobat-reader (Adobe Acrobat Reader) - 25.001.20937 - https://helpx.adobe.com/security/products/acrobat.html
- [ ] 7zip (7-Zip) - 25.00 - https://www.7-zip.org/history.txt
- [ ] winrar (WinRAR) - 7.13 - https://www.win-rar.com/whatsnew.html
- [ ] zoom (Zoom) - 6.5.0 - https://www.zoom.com/en/trust/security-bulletin/ (check the registry DisplayVersion format on a real PC)
- [ ] oracle-java (Oracle Java (JRE)) - 8.0.4710 - https://www.oracle.com/security-alerts/ (registry version is 8.0.<update>0.<build>)
- [ ] vlc (VLC media player) - 3.0.21 - https://www.videolan.org/security/
- [ ] ms-office (Microsoft Office / Microsoft 365) - 16.0.14332.21000 - https://learn.microsoft.com/en-us/officeupdates/microsoft365-apps-security-updates (floor set low so patched LTSC 2021 is not flagged)
- [ ] anydesk (AnyDesk) - 8.0.8 - https://anydesk.com/en/changelog/windows
- [ ] teamviewer (TeamViewer) - 15.67 - https://www.teamviewer.com/en/resources/trust-center/security-bulletins/

Also check on prep night:

- [ ] `os.min_supported_build.win11` (22631) is still the oldest serviced Windows 11 build.
- [ ] `asr.recommended` GUIDs match Microsoft's ASR rules reference.
- [ ] Every `name_regex` matches the DisplayName the collector reports on both dev machines.
