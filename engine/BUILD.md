# Building engine.exe (Brick A, manual s2.12)

One-folder PyInstaller build: `dist/engine/engine.exe` plus `dist/engine/_internal/`
(Python runtime, templates, schemas). One-folder, not one-file: it starts in well under
a second and does not unpack to `%TEMP%` on every run (fewer antivirus false positives).
`upx=False` for the same reason.

## Build

```powershell
# cwd: antigravity/engine
.venv\Scripts\pyinstaller engine.spec --clean --noconfirm
```

PyInstaller is pinned in `requirements-dev.txt` (6.11.1). Build on Windows to get a
Windows `engine.exe`; PyInstaller does not cross-compile (a macOS build produces
`dist/engine/engine`, useful only for checking the spec).

What `engine.spec` bundles (paths inside `_internal/`):

| Source | Bundled as |
|---|---|
| `engine/antigravity_engine/templates/` | `antigravity_engine/templates/` |
| `shared/contract/scan.schema.json` | `contract/scan.schema.json` |
| `shared/contract/report.schema.json` | `contract/report.schema.json` |
| `baseline/software-baseline.schema.json` | `contract/software-baseline.schema.json` |

Excluded: `tkinter`, `unittest`, `pytest`. The baseline data file is **not** bundled;
it ships next to the engine so it can be updated without a rebuild.

## Smoke test

```powershell
# cwd: antigravity/engine
dist\engine\engine.exe --version
dist\engine\engine.exe --in ..\shared\fixtures\scan.healthy.json --out ..\out\exe-test --baseline ..\baseline\software-baseline.json
```

Pass: `--version` prints `antigravity-engine <ver> contract <ver>`; `..\out\exe-test\`
holds `report.json`, `report.html` and `action-plan.pdf`; the PDF is one page; exit
code 0; the run takes under 5 s. To time it:

```powershell
Measure-Command { dist\engine\engine.exe --in ..\shared\fixtures\scan.healthy.json --out ..\out\exe-test --baseline ..\baseline\software-baseline.json }
```

Check the output against the contract:

```powershell
.venv\Scripts\python tools\validate.py report ..\out\exe-test\report.json
```

## How paths resolve when frozen (`antigravity_engine/paths.py`)

Frozen means `sys.frozen` is set and `sys._MEIPASS` exists (that is, `_internal/`).

| What | Frozen | Dev (`python -m antigravity_engine`) |
|---|---|---|
| scan / report schema | `<_MEIPASS>/contract/<name>` | `<repo>/shared/contract/<name>` |
| baseline schema | `<_MEIPASS>/contract/software-baseline.schema.json` | `<repo>/baseline/software-baseline.schema.json` |
| HTML template | `<_MEIPASS>/antigravity_engine/templates/` (relative to `render/html.py`) | `engine/antigravity_engine/templates/` |
| baseline data | `--baseline PATH`; if omitted, `<engine folder>/../baseline/software-baseline.json` | `--baseline PATH`; if omitted, `<repo>/baseline/software-baseline.json` |

The default frozen baseline path matches the installed layout (s5.4):
`resources/engine/engine.exe` -> `resources/baseline/software-baseline.json`. Run straight
from `dist\engine\` there is no `dist\baseline\`, so always pass `--baseline` there
(the desktop app passes it explicitly too). `tests/test_paths.py` covers both modes.

## No-Python verification (run by hand, not automated)

Copy `engine\dist\engine\` (the whole folder), `baseline\software-baseline.json` and
`shared\fixtures\scan.healthy.json` into the clean machine, e.g. `C:\ag\engine\`,
`C:\ag\baseline\`, `C:\ag\scan.healthy.json`. Confirm Python is absent first:
`where python` prints nothing, or only the Microsoft Store alias stub.

1. Windows Sandbox (Windows Pro; enable once, elevated, reboot:
   `Enable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM`).
   Inside the sandbox:

   ```powershell
   cd C:\ag; Measure-Command { .\engine\engine.exe --in .\scan.healthy.json --out .\out --baseline .\baseline\software-baseline.json }; .\engine\engine.exe --version; dir .\out
   ```

2. Schwan's clean VM (s1.2 step 13), same folder layout:

   ```powershell
   cd C:\ag; Measure-Command { .\engine\engine.exe --in .\scan.healthy.json --out .\out --baseline .\baseline\software-baseline.json }; .\engine\engine.exe --version; dir .\out
   ```

Pass criteria (s2.12 step 7): version prints, all three output files exist, the PDF
opens, total run < 5 s.

## What Schwan (Brick D) receives

`engine/dist/engine/`, the **whole folder**: `engine.exe` and `_internal/`. `engine.exe`
alone will not start. It goes to `resources/engine/` in the installer (s5.4), with
`baseline/software-baseline.json` at `resources/baseline/`. Hand it over only from a
commit on `main` (s1.9).
