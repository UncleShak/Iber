# installer/build-all.ps1   - run from repo root
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent

Write-Host '0/7 Contract check';    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot\contract-check.ps1"; if ($LASTEXITCODE) { exit 1 }
Write-Host '1/7 Engine tests';      & "$root\engine\.venv\Scripts\python.exe" -m pytest -q "$root\engine\tests"; if ($LASTEXITCODE) { exit 1 }
# The installer targets x64 only; an ARM64 venv would silently produce an ARM64 engine.exe.
$arch = & "$root\engine\.venv\Scripts\python.exe" -c "import platform; print(platform.machine())"
if ($LASTEXITCODE -or "$arch".Trim() -ne 'AMD64') { Write-Host "engine venv is not x64 (platform.machine() = '$arch')"; exit 1 }
Write-Host '2/7 Engine exe';        Push-Location "$root\engine"; & .venv\Scripts\pyinstaller.exe engine.spec --clean --noconfirm; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
# PE header: e_lfanew at 0x3C, Machine field at PE+4; 0x8664 = IMAGE_FILE_MACHINE_AMD64.
$b = [IO.File]::ReadAllBytes("$root\engine\dist\engine\engine.exe")
$pe = [BitConverter]::ToInt32($b, 0x3C)
if ([BitConverter]::ToUInt16($b, $pe + 4) -ne 0x8664) { Write-Host 'engine.exe is not x64'; exit 1 }
Write-Host '3/7 Resource manifest'; Push-Location "$root\desktop"; node ..\installer\make-manifest.mjs; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
Write-Host '4/7 Collector tests';   & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$root\collector\tests\Test-ReadOnly.ps1"; if ($LASTEXITCODE) { exit 1 }
                                    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$root\collector\tests\Test-Collector.ps1"; if ($LASTEXITCODE) { exit 1 }
Write-Host '5/7 Desktop install';   Push-Location "$root\desktop"; npm ci --prefer-offline; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
Write-Host '6/7 Desktop tests';     Push-Location "$root\desktop"; npm run typecheck; if ($LASTEXITCODE) { Pop-Location; exit 1 }; npm run test; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
Write-Host '7/7 Installer';         Push-Location "$root\desktop"; npm run dist; $c=$LASTEXITCODE; Pop-Location; if ($c) { exit 1 }
& "$PSScriptRoot\checksums.ps1"
Write-Host "DONE -> desktop\release" -ForegroundColor Green
