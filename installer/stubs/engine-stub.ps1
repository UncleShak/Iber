# installer/stubs/engine-stub.ps1
# Stub engine for Brick D isolation testing (AG_STUB=1).
# Takes --in/--out/--baseline, waits ~1s, writes report.stub.json, evidence.stub.json,
# and dummy report.html and action-plan.pdf into --out.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$In,
    
    [Parameter(Mandatory=$true)]
    [string]$Out,
    
    [Parameter(Mandatory=$true)]
    [string]$Baseline
)

$ErrorActionPreference = 'Stop'

Start-Sleep -Seconds 1

# Copy stub fixtures to output
$reportStub = Join-Path $PSScriptRoot "report.stub.json"
$evidenceStub = Join-Path $PSScriptRoot "evidence.stub.json"

if (-not (Test-Path $reportStub)) {
    Write-Error "Stub fixture not found: $reportStub"
    exit 1
}

Copy-Item -Path $reportStub -Destination (Join-Path $Out "report.json") -Force
Copy-Item -Path $evidenceStub -Destination (Join-Path $Out "evidence.json") -Force

# Create dummy HTML and PDF
@"
<!DOCTYPE html>
<html>
<head><title>Stub Report</title></head>
<body>
<h1>Stub Report</h1>
<p>This is a stub report for testing.</p>
</body>
</html>
"@ | Set-Content -Path (Join-Path $Out "report.html") -Encoding UTF8

# Minimal PDF (just enough to open)
"%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
190
%%EOF
" | Set-Content -Path (Join-Path $Out "action-plan.pdf") -Encoding ASCII

exit 0
