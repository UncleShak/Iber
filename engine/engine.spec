# engine/engine.spec - PyInstaller one-folder build (s2.12). See BUILD.md.
# cwd: antigravity/engine
#   .venv\Scripts\pyinstaller engine.spec --clean --noconfirm
from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    ["antigravity_engine/__main__.py"],
    pathex=[str(Path(SPECPATH))],
    datas=[
        ("antigravity_engine/templates", "antigravity_engine/templates"),
        (str(ROOT / "shared/contract/scan.schema.json"), "contract"),
        (str(ROOT / "shared/contract/report.schema.json"), "contract"),
        (str(ROOT / "shared/contract/evidence.schema.json"), "contract"),
        (str(ROOT / "baseline/software-baseline.schema.json"), "contract"),
    ],
    hiddenimports=[],
    excludes=["tkinter", "unittest", "pytest"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="engine",
          console=True, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name="engine", upx=False)
