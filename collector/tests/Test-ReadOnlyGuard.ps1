# Phase 2 tests for tests/Test-ReadOnly.ps1 (manual 3.7). Most cases call Invoke-AgReadOnlyScan in-process; the cases listed in $childCases run the real guard in a child powershell.exe
$ErrorActionPreference = 'Stop'
$collRoot = Split-Path -Parent $PSScriptRoot
$guard = Join-Path $PSScriptRoot 'Test-ReadOnly.ps1'
. $guard -NoRun    # defines Invoke-AgReadOnlyScan only
$script:CurrentCase = $null
# Cases that run the real guard as a child process (exit code, exact stdout, stderr, parse error, empty roots, leaks).
$childCases = @(
    'Real collector passes with exactly READ-ONLY OK', 'Verb Set- is flagged (Set-ItemProperty)', 'Cmdlet flagged: Invoke-WebRequest',
    'Literal in string: Win32_Product', 'Parse error fails', 'Bad files under tests and mocks are ignored',
    'Root below a parent folder named tests is still scanned', 'Root with no .ps1 files fails',
    'Root with only tests and mocks scripts fails', 'Failure output has no absolute root path and no user name'
)

$script:passed = 0
$script:failed = 0
function Test-Case([string]$Name, [scriptblock]$Body) {
    $script:CurrentCase = $Name
    try {
        & $Body | Out-Null
        Write-Output "PASS $Name"
        $script:passed++
    } catch {
        $m = ($_.Exception.Message -split "`r?`n")[0]
        Write-Output "FAIL ${Name}: $m"
        $script:failed++
    }
}
function Assert-True($Cond, [string]$Msg) { if (-not $Cond) { throw $Msg } }
function Assert-Run { if (-not [IO.File]::Exists($guard)) { throw 'Test-ReadOnly.ps1 does not exist' } }

function New-TempDir {
    $d = Join-Path ([IO.Path]::GetTempPath()) ('ag-test-' + [Guid]::NewGuid().ToString('N'))
    [void][IO.Directory]::CreateDirectory($d)
    return $d
}
function Invoke-Native([string[]]$ArgList) {
    $prevEap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    try { $all = & powershell.exe @ArgList 2>&1; $code = $LASTEXITCODE } finally { $ErrorActionPreference = $prevEap }
    $outL = @($all | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] } | ForEach-Object { [string]$_ })
    $errL = @($all | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] } | ForEach-Object { ([string]$_).Trim() })
    [pscustomobject]@{ Code = $code; Lines = $outL; Text = ($outL -join "`n"); Err = ($errL -join "`n") }
}
function Write-TestFile([string]$Root, [string]$Rel, [string]$Content) {
    $p = Join-Path $Root $Rel
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($p))
    [IO.File]::WriteAllText($p, $Content, (New-Object Text.UTF8Encoding $false))
}
function Invoke-GuardInProc([string]$Root) {
    try { $lines = @(Invoke-AgReadOnlyScan $Root); $code = 0 } catch { $lines = @('guard internal error'); $code = 1 }
    if ($code -eq 0 -and $lines.Count -gt 0) { $code = 1 }
    if ($code -eq 0) { $lines = @('READ-ONLY OK') }
    [pscustomobject]@{ Code = $code; Lines = $lines; Text = ($lines -join "`n"); Err = '' }
}
function Invoke-Guard([string]$Root) {
    Assert-Run
    if ($childCases -contains $script:CurrentCase) { return (Invoke-Native @('-NoProfile', '-File', $guard, '-Root', $Root)) }
    Invoke-GuardInProc $Root
}
# Runs the guard on a temp root holding the given files (relative path -> content). Returns the result.
function Invoke-GuardOn([hashtable]$Files, [string]$SubRoot = '') {
    Assert-Run
    $dir = New-TempDir
    try {
        $root = $dir
        if ($SubRoot) { $root = Join-Path $dir $SubRoot; [void][IO.Directory]::CreateDirectory($root) }
        foreach ($k in $Files.Keys) { Write-TestFile $root $k $Files[$k] }
        Invoke-Guard $root
    } finally { [IO.Directory]::Delete($dir, $true) }
}
# Three lines: two harmless ones, then the statement under test on line 3.
function Line3([string]$Stmt) { "# header`r`nWrite-Output 1`r`n$Stmt`r`n" }
function Assert-Flagged($r, [string]$File, [int]$Line, [string]$Needle) {
    Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
    $pat = '(?im)^' + [regex]::Escape($File) + ':' + $Line + '\s.*' + [regex]::Escape($Needle)
    Assert-True ($r.Text -match $pat) "no '$File`:$Line ... $Needle' in output: $($r.Text -replace "`n",' | ')"
}
function Assert-Passes($r) {
    Assert-True ($r.Code -eq 0) "exit code was $($r.Code): $($r.Text -replace "`n",' | ')"
    Assert-True ($r.Text -eq 'READ-ONLY OK') "output was '$($r.Text)'"
}
function Flag-Case([string]$Stmt, [string]$Needle, [string]$File = 'bad.ps1') {
    $r = Invoke-GuardOn @{ $File = (Line3 $Stmt) }
    Assert-Flagged $r $File 3 $Needle
}

# ---- 1 real collector ----
Test-Case 'Real collector passes with exactly READ-ONLY OK' {
    Assert-Run
    $r = Invoke-Native @('-NoProfile', '-File', $guard)
    Assert-True ($r.Code -eq 0) "exit code was $($r.Code): $($r.Text -replace "`n",' | ')"
    Assert-True ($r.Text -eq 'READ-ONLY OK') "output was '$($r.Text)'"
}

# ---- 2 forbidden verbs ----
$verbCalls = [ordered]@{
    'Set' = 'Set-ItemProperty -Path x -Name y'; 'New' = 'New-Item -Path x'; 'Remove' = 'Remove-Item x'
    'Add' = 'Add-Content -Path x'; 'Clear' = 'Clear-Content x'; 'Enable' = 'Enable-NetFirewallRule -Name x'
    'Disable' = 'Disable-NetAdapter -Name x'; 'Start' = 'Start-Service x'; 'Stop' = 'Stop-Service x'
    'Restart' = 'Restart-Service x'; 'Suspend' = 'Suspend-BitLocker -MountPoint C:'; 'Resume' = 'Resume-BitLocker -MountPoint C:'
    'Install' = 'Install-Module x'; 'Uninstall' = 'Uninstall-Module x'; 'Update' = 'Update-Help'
    'Register' = 'Register-ScheduledTask -TaskName x'; 'Unregister' = 'Unregister-ScheduledTask -TaskName x'
}
foreach ($v in $verbCalls.Keys) {
    $stmt = $verbCalls[$v]
    Test-Case "Verb $v- is flagged ($($stmt.Split(' ')[0]))" {
        Flag-Case $stmt $stmt.Split(' ')[0]
    }
}

# ---- 3 named forbidden cmdlets ----
foreach ($c in @('Invoke-WebRequest http://x', 'Invoke-RestMethod http://x', 'Invoke-Expression $x', 'Start-Process notepad', 'Add-Type -TypeDefinition x')) {
    Test-Case "Cmdlet flagged: $($c.Split(' ')[0])" { Flag-Case $c $c.Split(' ')[0] }
}

# ---- 4 aliases ----
foreach ($a in @(@('iwr http://x', 'iwr'), @('rm x', 'rm'), @('sc x', 'sc'), @('iex $x', 'iex'), @('1 | % { $_ }', '%'))) {
    Test-Case "Alias flagged: $($a[1])" { Flag-Case $a[0] $a[1] }
}

# ---- 5 external programs ----
foreach ($e in @(@('vssadmin.exe list shadows', 'vssadmin'), @('cmd.exe /c dir', 'cmd.exe'), @('bcdedit /enum', 'bcdedit'))) {
    Test-Case "External program flagged: $($e[1])" { Flag-Case $e[0] $e[1] }
}

# ---- 6 forbidden literals, in a string and in a comment ----
$literals = @(
    @('Win32_Product', 'Win32_Product'), @('vssadmin', 'vssadmin'), @('wbadmin start', 'wbadmin'), @('manage-bde', 'manage-bde'),
    @('bcdedit', 'bcdedit'), @('Checkpoint-Computer', 'Checkpoint-Computer'), @('reagentc /enable', 'reagentc'),
    @('reagentc /disable', 'reagentc'), @('-EncodedCommand', 'EncodedCommand'), @('-WindowStyle Hidden', 'WindowStyle'), @('RunAs', 'runas')
)
foreach ($l in $literals) {
    Test-Case "Literal in string: $($l[0])" {
        $r = Invoke-GuardOn @{ 'bad.ps1' = (Line3 "`$x = 'see $($l[0]) here'") }
        Assert-Flagged $r 'bad.ps1' 3 $l[1]
    }
    Test-Case "Literal in comment: $($l[0])" {
        $r = Invoke-GuardOn @{ 'bad.ps1' = (Line3 "# see $($l[0]) here") }
        Assert-Flagged $r 'bad.ps1' 3 $l[1]
    }
}

# ---- 7 reagentc ----
$reOk = 'function Read-AgReagentc { & "$env:SystemRoot\System32\reagentc.exe" /info 2>&1 | ForEach-Object { "$_" } }'
Test-Case 'reagentc /info 2>&1 passes in lib\Common.ps1' {
    Assert-Passes (Invoke-GuardOn @{ 'lib\Common.ps1' = "$reOk`r`n" })
}
Test-Case 'reagentc /info without redirection passes in lib\Common.ps1' {
    Assert-Passes (Invoke-GuardOn @{ 'lib\Common.ps1' = "function Read-AgReagentc { & `"`$env:SystemRoot\System32\reagentc.exe`" /info }`r`n" })
}
foreach ($arg in @('/info /extra', '/boottore', '/info /boottore 2>&1', '/enable')) {
    Test-Case "reagentc with '$arg' fails" {
        $r = Invoke-GuardOn @{ 'lib\Common.ps1' = "# h`r`nfunction Read-AgReagentc {`r`n & `"`$env:SystemRoot\System32\reagentc.exe`" $arg`r`n}`r`n" }
        Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
        Assert-True ($r.Text -match '(?i)lib\\Common\.ps1:3\s') "no violation at lib\Common.ps1:3: $($r.Text -replace "`n",' | ')"
    }
}
Test-Case 'reagentc /info in an unpinned file fails' {
    $r = Invoke-GuardOn @{ 'other.ps1' = "# h`r`nWrite-Output 1`r`n& `"`$env:SystemRoot\System32\reagentc.exe`" /info`r`n" }
    Assert-Flagged $r 'other.ps1' 3 'dynamic'
}

# ---- 8 dynamic invocation ----
foreach ($d in @('& $x', "& ('Set-'+'Item') x", '. $somePath', '& $Body')) {
    Test-Case "Dynamic call flagged: $d" { Flag-Case $d 'dynamic' }
}

# ---- 9 own functions ----
Test-Case 'Own function defined and called passes' {
    Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = "function Get-AgFoo { Write-Output 1 }`r`nGet-AgFoo`r`n" })
}
Test-Case 'Own function defined in another file and called passes' {
    Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = "Get-AgFoo`r`n"; 'lib\b.ps1' = "function Get-AgFoo { Write-Output 1 }`r`n" })
}
Test-Case 'Function called but not defined fails' {
    Flag-Case 'Get-AgNotDefined' 'Get-AgNotDefined'
}
Test-Case 'Defining function Set-AgThing fails' {
    Flag-Case 'function Set-AgThing { Write-Output 1 }' 'Set-AgThing'
}
Test-Case 'Defining function Remove-Item (shadowing) fails' {
    Flag-Case 'function Remove-Item { Write-Output 1 }' 'Remove-Item'
}
Test-Case 'Defining function Get-Service (shadowing) fails' {
    Flag-Case 'function Get-Service { Write-Output 1 }' 'Get-Service'
}
Test-Case 'Defining function Invoke-WebRequest fails' {
    Flag-Case 'function Invoke-WebRequest { Write-Output 1 }' 'Invoke-WebRequest'
}

# ---- 10 .NET types and members ----
$netCases = @(
    @('[IO.File]::Delete("x")', 'IO.File'), @('[IO.Directory]::CreateDirectory("x")', 'IO.Directory'),
    @('[Diagnostics.Process]::Start("x")', 'Diagnostics.Process'), @('$w = [Net.WebClient]::new()', 'Net.WebClient'),
    @('[Microsoft.Win32.Registry]::SetValue("a","b",1)', 'Microsoft.Win32.Registry'), @('[scriptblock]::Create("1")', 'scriptblock'),
    @('[Environment]::SetEnvironmentVariable("a","b")', 'Environment'), @('[IO.File]::WriteAllText("a","b")', 'IO.File'),
    @('$t = [IO.File]', 'IO.File'), @('[IO.File]::ReadAllText("a")', 'IO.File')
)
foreach ($n in $netCases) {
    Test-Case ".NET flagged: $($n[0])" { Flag-Case $n[0] $n[1] }
}
Test-Case '[IO.File]::WriteAllText inside Write-ScanJson passes' {
    Assert-Passes (Invoke-GuardOn @{ 'lib\Common.ps1' = "function Write-ScanJson(`$Scan) {`r`n [IO.File]::WriteAllText('a', 'b')`r`n}`r`n" })
}
Test-Case '[IO.File]::WriteAllText in another function fails' {
    $r = Invoke-GuardOn @{ 'lib\Common.ps1' = "function Other {`r`n [IO.File]::WriteAllText('a', 'b')`r`n}`r`n" }
    Assert-Flagged $r 'lib\Common.ps1' 2 'IO.File'
}
Test-Case 'Param type [scriptblock] is allowed' {
    Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = "function Run-It([scriptblock]`$Body, [string]`$S, [switch]`$W, [bool]`$B) { Write-Output `$S }`r`n" })
}

# ---- 11 New-Object and member names ----
Test-Case 'New-Object -ComObject Shell.Application passes' {
    Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = "`$s = New-Object -ComObject Shell.Application`r`n" })
}
Test-Case 'New-Object Text.UTF8Encoding $false passes' {
    Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = "`$s = (New-Object Text.UTF8Encoding `$false)`r`n" })
}
foreach ($c in @(@('New-Object -ComObject WScript.Shell', 'New-Object'), @('New-Object Net.WebClient', 'New-Object'),
        @('New-Object -ComObject Shell.Application -Strict', 'New-Object'))) {
    Test-Case "New-Object flagged: $($c[0])" { Flag-Case $c[0] $c[1] }
}
foreach ($m in @('ShellExecute', 'InvokeVerb', 'InvokeVerbEx', 'ShellExecuteEx', 'Run', 'Exec', 'SetValue', 'CreateSubKey',
        'DeleteSubKey', 'DeleteSubKeyTree', 'DeleteValue', 'Delete', 'Kill', 'InvokeScript', 'NewScriptBlock')) {
    Test-Case "Member .$m(...) flagged" { Flag-Case "`$o.$m('x')" $m }
}

# ---- 12 parse error ----
Test-Case 'Parse error fails' {
    $r = Invoke-GuardOn @{ 'bad.ps1' = "function Broken {`r`n Write-Output 1`r`n" }
    Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
    Assert-True ($r.Text -match '(?i)bad\.ps1:\d+\s') "no violation line: $($r.Text -replace "`n",' | ')"
}

# ---- 13 tests and mocks ignored ----
Test-Case 'Bad files under tests\ and mocks\ are ignored' {
    $r = Invoke-GuardOn @{ 'ok.ps1' = "Write-Output 1`r`n"; 'tests\bad.ps1' = "Remove-Item x`r`n"; 'mocks\bad.ps1' = "Remove-Item x`r`n"; 'Tests\Sub\bad.ps1' = "Remove-Item x`r`n" }
    Assert-Passes $r
}
Test-Case 'A folder merely containing "tests" in its name is scanned' {
    $r = Invoke-GuardOn @{ 'ok.ps1' = "Write-Output 1`r`n"; 'lib\tests\bad.ps1' = (Line3 'Remove-Item x') }
    Assert-Flagged $r 'lib\tests\bad.ps1' 3 'Remove-Item'
}

# ---- 14 root under a parent named tests ----
Test-Case 'Root below a parent folder named tests is still scanned' {
    $r = Invoke-GuardOn @{ 'bad.ps1' = (Line3 'Remove-Item x') } 'tests\collector'
    Assert-Flagged $r 'bad.ps1' 3 'Remove-Item'
}

# ---- 15 no vacuous OK ----
Test-Case 'Root with no .ps1 files fails' {
    $r = Invoke-GuardOn @{ 'readme.txt' = 'hello' }
    Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
    Assert-True ($r.Text -notmatch 'READ-ONLY OK') 'printed OK'
}
Test-Case 'Root with only tests\ and mocks\ scripts fails' {
    $r = Invoke-GuardOn @{ 'tests\a.ps1' = "Write-Output 1`r`n"; 'mocks\b.ps1' = "Write-Output 1`r`n" }
    Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
}

# ---- 16 no leaks in output ----
Test-Case 'Failure output has no absolute root path and no user name' {
    Assert-Run
    $dir = New-TempDir
    try {
        Write-TestFile $dir 'bad.ps1' (Line3 'Remove-Item x')
        Write-TestFile $dir 'broken.ps1' "function Broken {`r`n"
        Write-TestFile $dir 'lit.ps1' "# vssadmin`r`n"
        $r = Invoke-Guard $dir
        Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
        $all = $r.Text + "`n" + $r.Err
        Assert-True ($all.Contains('bad.ps1:3')) 'no relative violation'
        Assert-True (-not $all.Contains($dir)) 'output contains absolute root'
        Assert-True (-not $all.Contains([IO.Path]::GetTempPath())) 'output contains temp path'
        Assert-True ($all -notmatch ('(?i)(?<![A-Za-z0-9])' + [regex]::Escape($env:USERNAME) + '(?![A-Za-z0-9])')) 'output contains user name'
    } finally { [IO.Directory]::Delete($dir, $true) }
}

# =====================================================================================================
# Round 2: bypasses found by Socrates (b01-b14), pin abuse, and allowlist-style rules
# =====================================================================================================
function Lines([string[]]$L) { ($L -join "`r`n") + "`r`n" }
function Assert-FlaggedAny($r, [string]$File, [string]$Needle) {
    Assert-True ($r.Code -eq 1) "exit code was $($r.Code): $($r.Text -replace "`n",' | ')"
    $pat = '(?im)^' + [regex]::Escape($File) + ':\d+\s.*' + [regex]::Escape($Needle)
    Assert-True ($r.Text -match $pat) "no '$File`:<n> ... $Needle' in output: $($r.Text -replace "`n",' | ')"
}
function Flag-Files([hashtable]$Files, [string]$File, [string]$Needle) {
    Assert-FlaggedAny (Invoke-GuardOn $Files) $File $Needle
}

# b01 ForEach-Object member-name forms
Test-Case 'b01 ForEach-Object Stop (positional member name) flagged' { Flag-Case 'Get-Service -Name Spooler | ForEach-Object Stop' 'ForEach-Object' }
Test-Case 'b01 ForEach-Object -MemberName Delete flagged' { Flag-Case 'Get-ChildItem -Path C:\x\a.txt | ForEach-Object -MemberName Delete' 'ForEach-Object' }

# b02 reflection through type objects
Test-Case 'b02 [regex].Assembly flagged' { Flag-Case "`$p = [regex].Assembly.GetType('System.Diagnostics.Process')" 'Assembly' }
Test-Case 'b02 $var::Start flagged' { Flag-Case "`$p::Start('calc.exe')" 'static' }
Test-Case 'b02 $var::WriteAllText flagged' { Flag-Case "`$f::WriteAllText('C:\x\y.txt', 'z')" 'static' }
Test-Case 'b02 GetType with an argument flagged' { Flag-Case "`$t = (Get-Culture).GetType('System.IO.File')" 'GetType' }

# b03 file redirection
Test-Case 'b03 > file redirection flagged' { Flag-Case "Write-Output 'data' > C:\x\out.txt" 'redirection' }
Test-Case 'b03 >> file redirection flagged' { Flag-Case "Write-Output 'data' >> C:\x\out.txt" 'redirection' }
Test-Case 'b03 2>&1 merging redirection is fine' { Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = "Write-Output 1 2>&1`r`n" }) }

# b04 drive-qualified variables
foreach ($v in @('${C:\x\written.txt} = ''content''', '${function:Evil} = { 1 }', '${variable:Zed} = 1', '$x = ${C:\x\y.txt}')) {
    Test-Case "b04 drive variable flagged: $($v.Substring(0, [Math]::Min(22, $v.Length)))" { Flag-Case $v 'variable' }
}
Test-Case '$env: read is fine' { Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = "`$x = `$env:SystemDrive`r`n" }) }

# b05 / reflective properties, $ExecutionContext, $Host, $PSCmdlet
Test-Case 'b05 $ExecutionContext.InvokeProvider flagged' { Flag-Case "`$ExecutionContext.InvokeProvider.Item.Remove('C:\x\a.txt', `$false)" 'InvokeProvider' }
Test-Case '$ExecutionContext outside Write-ScanJson flagged' { Flag-Case "`$ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath('x')" 'ExecutionContext' }
Test-Case '$ExecutionContext in Write-ScanJson in a non-Common file flagged' {
    Flag-Files @{ 'bad.ps1' = (Lines @('# h', 'Write-Output 1', 'function Write-ScanJson($Path) {', ' $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)', '}')) } 'bad.ps1' 'ExecutionContext'
}
Test-Case '$ExecutionContext other chain inside Write-ScanJson flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Write-ScanJson($Path) {', ' $ExecutionContext.InvokeCommand.GetCommand(''x'', 1)', '}')) } 'lib\Common.ps1' 'ExecutionContext'
}
Test-Case '$ExecutionContext exact chain inside Write-ScanJson passes' {
    Assert-Passes (Invoke-GuardOn @{ 'lib\Common.ps1' = (Lines @('function Write-ScanJson($Path) {', ' $full = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)', '}')) })
}
Test-Case '$Host flagged' { Flag-Case '$h = $Host' 'Host' }
Test-Case '$PSCmdlet flagged' { Flag-Case '$h = $PSCmdlet' 'PSCmdlet' }
foreach ($p in @('Assembly', 'ImplementingType', 'InvokeProvider', 'InvokeCommand', 'Module', 'ScriptBlock', 'PSObject', 'Methods', 'DeclaringType', 'UnderlyingSystemType', 'BaseType')) {
    Test-Case "Reflective property .$p flagged" { Flag-Case "`$x = `$o.$p" $p }
}

# b06 methods on cmdlet output
Test-Case 'b06 (Get-Service).Stop() flagged' { Flag-Case '(Get-Service -Name Spooler).Stop()' 'Stop' }
Test-Case 'b06 (Get-ChildItem).MoveTo() flagged' { Flag-Case "(Get-ChildItem C:\x\a.txt).MoveTo('C:\x\b.txt')" 'MoveTo' }
foreach ($m in @('Start', 'Create', 'Invoke', 'GetType', 'AddScript')) {
    Test-Case "Method .$m() not in allowlist flagged" { Flag-Case "`$o.$m()" $m }
}
Test-Case 'Allowed instance methods pass' {
    Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = "`$s = (Get-Random -Maximum 5).ToString('x4')`r`n`$t = `$s.Substring(0, 1)`r`n" })
}

# b07 COM chains
Test-Case 'b07 COM .Verbs() flagged' { Flag-Case "`$sh.NameSpace('C:\x').ParseName('a.exe').Verbs().Item(0).DoIt()" 'Verbs' }
Test-Case 'b07 COM .DoIt() flagged' { Flag-Case "`$sh.NameSpace('C:\x').ParseName('a.exe').Verbs().Item(0).DoIt()" 'DoIt' }
Test-Case 'b07 COM .ServiceStop() flagged' { Flag-Case "`$sh.ServiceStop('Spooler', `$false)" 'ServiceStop' }

# b08 CIM
Test-Case 'b08 computed -ClassName flagged' { Flag-Case "Get-CimInstance -ClassName ('Win32_Prod' + 'uct')" 'Get-CimInstance' }
Test-Case 'b08 -ComputerName flagged' { Flag-Case 'Get-CimInstance -ClassName Win32_OperatingSystem -ComputerName evil.example' 'ComputerName' }
foreach ($p in @('ComputerName', 'CimSession', 'Session', 'Query', 'Credential')) {
    Test-Case "Parameter -$p flagged on any command" { Flag-Case "Get-Service -$p x" $p }
}
Test-Case 'Splatting flagged' { Flag-Case 'Get-Service @a' 'splat' }
Test-Case 'Get-CimInstance class outside the list flagged' { Flag-Case 'Get-CimInstance -ClassName Win32_Process' 'Get-CimInstance' }
Test-Case 'Get-CimInstance namespace outside the list flagged' { Flag-Case 'Get-CimInstance -ClassName Win32_OperatingSystem -Namespace root\wmi' 'Get-CimInstance' }
Test-Case 'Get-CimInstance positional class flagged' { Flag-Case 'Get-CimInstance Win32_OperatingSystem' 'Get-CimInstance' }
Test-Case 'Get-CimInstance without -ClassName flagged' { Flag-Case 'Get-CimInstance -Namespace root/cimv2' 'Get-CimInstance' }
Test-Case 'Get-CimInstance allowed forms pass' {
    Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = (Lines @('Get-CimInstance -ClassName Win32_OperatingSystem', 'Get-CimInstance -ClassName Win32_ShadowCopy', 'Get-CimInstance -Namespace root\SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction SilentlyContinue')) })
}
Test-Case 'ForEach-Object with a scriptblock passes' { Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = "1 | ForEach-Object { `$_ }`r`n" }) }

# b09 temp files
Test-Case 'b09 [IO.Path]::GetTempFileName flagged' { Flag-Case '$t = [IO.Path]::GetTempFileName()' 'GetTempFileName' }

# b10 #requires
foreach ($rq in @('#requires -Modules SomeModule', '#requires -RunAsAdministrator', '#requires -PSEdition Desktop', '#requires -Version 5.1')) {
    Test-Case "b10 $rq flagged" {
        $r = Invoke-GuardOn @{ 'bad.ps1' = "$rq`r`nWrite-Output 1`r`n" }
        Assert-FlaggedAny $r 'bad.ps1' 'requires'
    }
}

# b13 / duplicate definitions
Test-Case 'b13 Write-ScanJson defined outside lib\Common.ps1 flagged' {
    Flag-Files @{ 'bad.ps1' = (Lines @('# h', 'Write-Output 1', 'function Write-ScanJson { [IO.File]::WriteAllText(''C:\x\x.txt'', ''y'') }')) } 'bad.ps1' 'Write-ScanJson'
}
Test-Case 'Invoke-Probe defined outside lib\Common.ps1 flagged' {
    Flag-Files @{ 'bad.ps1' = (Lines @('# h', 'Write-Output 1', 'function Invoke-Probe { Write-Output 1 }')) } 'bad.ps1' 'Invoke-Probe'
}
Test-Case 'Write-ScanJson and Invoke-Probe in lib\Common.ps1 pass' {
    Assert-Passes (Invoke-GuardOn @{ 'lib\Common.ps1' = (Lines @('function Write-ScanJson { Write-Output 1 }', 'function Invoke-Probe { Write-Output 1 }')) })
}
Test-Case 'Duplicate Write-ScanJson (Common.ps1 and another file) flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Write-ScanJson { Write-Output 1 }')); 'lib\More.ps1' = (Lines @('function Write-ScanJson { Write-Output 2 }')) } 'lib\More.ps1' 'more than once'
}
Test-Case 'Duplicate function across files flagged' {
    Flag-Files @{ 'a.ps1' = (Lines @('function Get-AgFoo { Write-Output 1 }')); 'b.ps1' = (Lines @('function Get-AgFoo { Write-Output 2 }')) } 'b.ps1' 'more than once'
}
Test-Case 'Duplicate function in one file flagged' {
    Flag-Files @{ 'a.ps1' = (Lines @('function Get-AgFoo { Write-Output 1 }', 'function Get-AgFoo { Write-Output 2 }')) } 'a.ps1' 'more than once'
}

# b14 $env: assignment and bare reagentc
Test-Case 'b14 $env:Path assignment flagged' { Flag-Case "`$env:Path = 'C:\Users\Public;' + `$env:Path" 'env' }
Test-Case '$env: compound assignment flagged' { Flag-Case "`$env:Path += 'x'" 'env' }
Test-Case 'b14 bare reagentc.exe /info flagged' { Flag-Case 'reagentc.exe /info' 'reagentc' }
Test-Case '$env:SystemRoot override before reagentc flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Read-AgReagentc {', ' $env:SystemRoot = ''C:\Users\Public\evil''', ' & "$env:SystemRoot\System32\reagentc.exe" /info 2>&1', '}')) } 'lib\Common.ps1' 'env'
}
Test-Case 'reagentc pin inside a non-Read-Ag function flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Other {', ' & "$env:SystemRoot\System32\reagentc.exe" /info 2>&1', '}')) } 'lib\Common.ps1' 'dynamic'
}

# unsafe path strings
foreach ($s in @('\\server\share\x', 'WSMan:\localhost', 'Cert:\CurrentUser\My', 'Function:\Evil', 'Variable:\Zed', 'Alias:\ls')) {
    Test-Case "Path string flagged: $s" { Flag-Case "`$x = '$s'" 'path' }
}
Test-Case 'Registry path strings are fine' { Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = "`$x = 'HKLM:\SOFTWARE\Microsoft'`r`n" }) }

# pin: & $probes[$key]
$probesGood = Lines @('$probes = [ordered]@{ a = { Write-Output 1 }; b = { Write-Output 2 } }', 'foreach ($key in $probes.Keys) {', ' & $probes[$key]', '}')
Test-Case 'Pin probes: scriptblock hashtable passes' { Assert-Passes (Invoke-GuardOn @{ 'collector.ps1' = $probesGood }) }
Test-Case 'Pin probes: non-scriptblock value flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @('$probes = @{ a = ''calc.exe'' }', '$key = ''a''', '& $probes[$key]')) } 'collector.ps1' 'dynamic'
}
Test-Case 'Pin probes: element reassigned flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @('$probes = @{ a = { Write-Output 1 } }', '$probes[''a''] = ''calc.exe''', '& $probes[$key]')) } 'collector.ps1' 'dynamic'
}
Test-Case 'Pin probes: assigned twice flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @('$probes = @{ a = { Write-Output 1 } }', '$probes = @{ a = { Write-Output 2 } }', '& $probes[$key]')) } 'collector.ps1' 'dynamic'
}
Test-Case 'Pin probes: inside a function flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @('$probes = @{ a = { Write-Output 1 } }', 'function Run-It { & $probes[$key] }')) } 'collector.ps1' 'dynamic'
}
Test-Case 'Pin probes: in another file flagged' { Flag-Files @{ 'other.ps1' = $probesGood } 'other.ps1' 'dynamic' }

# pin: probes loader
$loadGood = 'Get-ChildItem "$PSScriptRoot\probes\*.ps1" | ForEach-Object { . $_.FullName }'
Test-Case 'Pin loader: exact pipeline passes' { Assert-Passes (Invoke-GuardOn @{ 'collector.ps1' = (Lines @($loadGood)) }) }
Test-Case 'Pin loader: other source folder flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @('Get-ChildItem C:\x\calc.exe | ForEach-Object { . $_.FullName }')) } 'collector.ps1' 'dynamic'
}
Test-Case 'Pin loader: extra pipeline stage flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @('Get-ChildItem "$PSScriptRoot\probes\*.ps1" | Sort-Object | ForEach-Object { . $_.FullName }')) } 'collector.ps1' 'dynamic'
}
Test-Case 'Pin loader: in another file flagged' { Flag-Files @{ 'other.ps1' = (Lines @($loadGood)) } 'other.ps1' 'dynamic' }

# pin: Common.ps1 dot-source
Test-Case 'Pin Common: top level of collector.ps1 passes' { Assert-Passes (Invoke-GuardOn @{ 'collector.ps1' = (Lines @('. "$PSScriptRoot\lib\Common.ps1"')) }) }
Test-Case 'Pin Common: inside a function flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @('function Load-It {', ' . "$PSScriptRoot\lib\Common.ps1"', '}')) } 'collector.ps1' 'dynamic'
}
Test-Case 'Pin Common: in another file flagged' { Flag-Files @{ 'other.ps1' = (Lines @('. "$PSScriptRoot\lib\Common.ps1"')) } 'other.ps1' 'dynamic' }

# pin: mock dot-source
$mockLine = '. ([string](Resolve-Path $MockFile))'
Test-Case 'Pin mock: parameter, never assigned passes' {
    Assert-Passes (Invoke-GuardOn @{ 'collector.ps1' = (Lines @('param([string]$MockFile)', 'Write-Output 1', "if (`$MockFile) { $mockLine }")) })
}
Test-Case 'Pin mock: $MockFile assigned flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @('param([string]$MockFile)', '$MockFile = ''C:\x\evil.ps1''', $mockLine)) } 'collector.ps1' 'dynamic'
}
Test-Case 'Pin mock: r1 form, assigned and not a parameter, flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @('# h', '$MockFile = "$PSScriptRoot\mocks\evil.ps1"', $mockLine)) } 'collector.ps1' 'dynamic'
}
Test-Case 'Pin mock: $MockFile not a parameter flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @('# h', 'Write-Output 1', $mockLine)) } 'collector.ps1' 'dynamic'
}
Test-Case 'Pin mock: inside a function flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @('param([string]$MockFile)', "function Load-It { $mockLine }")) } 'collector.ps1' 'dynamic'
}

# pin: & $Body
Test-Case 'Pin Body: typed parameter in Invoke-Probe passes' {
    Assert-Passes (Invoke-GuardOn @{ 'lib\Common.ps1' = (Lines @('function Invoke-Probe {', ' param([scriptblock]$Body)', ' $d = & $Body', '}')) })
}
Test-Case 'Pin Body: untyped parameter flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Invoke-Probe {', ' param($Body)', ' $d = & $Body', '}')) } 'lib\Common.ps1' 'dynamic'
}
Test-Case 'Pin Body: [string] parameter flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Invoke-Probe {', ' param([string]$Body)', ' $d = & $Body', '}')) } 'lib\Common.ps1' 'dynamic'
}
Test-Case 'Pin Body: assigned inside Invoke-Probe flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Invoke-Probe {', ' param([scriptblock]$Body)', ' $Body = ''notepad.exe''', ' $d = & $Body', '}')) } 'lib\Common.ps1' 'dynamic'
}
Test-Case 'Pin Body: r1 form in another function flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Other { $Body = ''notepad.exe''; & $Body }')) } 'lib\Common.ps1' 'dynamic'
}
Test-Case 'Pin Body: in another file flagged' {
    Flag-Files @{ 'a.ps1' = (Lines @('function Other { param([scriptblock]$Body) & $Body }')) } 'a.ps1' 'dynamic'
}

# leaks
Test-Case 'No leak: & quoted path with the user name' {
    $r = Invoke-GuardOn @{ 'lib\Common.ps1' = (Lines @('function Read-AgReagentc {', " & 'C:\Users\$env:USERNAME\x.exe' /info 2>&1", '}')) }
    Assert-FlaggedAny $r 'lib\Common.ps1' 'command'
    Assert-True ($r.Text -notmatch ('(?i)(?<![A-Za-z0-9])' + [regex]::Escape($env:USERNAME) + '(?![A-Za-z0-9])')) 'user name leaked'
    Assert-True (-not $r.Text.Contains('Users')) 'path leaked'
}
Test-Case 'No leak: bare path call containing $env:USERNAME' {
    $r = Invoke-GuardOn @{ 'bad.ps1' = (Lines @('# h', 'Write-Output 1', 'C:\Users\$env:USERNAME\x.exe')) }
    Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
    Assert-True ($r.Text -notmatch ('(?i)(?<![A-Za-z0-9])' + [regex]::Escape($env:USERNAME) + '(?![A-Za-z0-9])')) 'user name leaked'
    Assert-True (-not $r.Text.Contains('Users')) 'path leaked'
}
Test-Case 'No leak: member name that is a path' {
    $r = Invoke-GuardOn @{ 'bad.ps1' = (Lines @('# h', 'Write-Output 1', "`$o.'C:\Users\$env:USERNAME\x'()")) }
    Assert-True ($r.Code -eq 1) "exit code was $($r.Code)"
    Assert-True ($r.Text -notmatch ('(?i)(?<![A-Za-z0-9])' + [regex]::Escape($env:USERNAME) + '(?![A-Za-z0-9])')) 'user name leaked'
    Assert-True (-not $r.Text.Contains('Users')) 'path leaked'
    Assert-True ($r.Text.Contains('<redacted>')) 'no <redacted> marker'
}

# pin: $p.PSObject.Properties as a foreach collection in Read-AgAsrRegistry
$psoGood = Lines @('function Read-AgAsrRegistry {', ' $p = Get-ItemProperty -Path x', ' foreach ($prop in $p.PSObject.Properties) { Write-Output 1 }', '}')
Test-Case 'Pin PSObject: foreach collection in Read-AgAsrRegistry passes' { Assert-Passes (Invoke-GuardOn @{ 'lib\Common.ps1' = $psoGood }) }
Test-Case 'Pin PSObject: .PSObject.Methods there flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Read-AgAsrRegistry {', ' $p = Get-ItemProperty -Path x', ' foreach ($prop in $p.PSObject.Methods) { Write-Output 1 }', '}')) } 'lib\Common.ps1' 'PSObject'
}
Test-Case 'Pin PSObject: .PSObject.BaseObject there flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Read-AgAsrRegistry {', ' $p = Get-ItemProperty -Path x', ' foreach ($prop in $p.PSObject.BaseObject) { Write-Output 1 }', '}')) } 'lib\Common.ps1' 'PSObject'
}
Test-Case 'Pin PSObject: not a foreach collection (assigned) flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Read-AgAsrRegistry {', ' $p = Get-ItemProperty -Path x', ' $q = $p.PSObject.Properties', '}')) } 'lib\Common.ps1' 'PSObject'
}
Test-Case 'Pin PSObject: inside the foreach body (not the collection) flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Read-AgAsrRegistry {', ' $p = Get-ItemProperty -Path x', ' foreach ($prop in 1) { $q = $p.PSObject.Properties }', '}')) } 'lib\Common.ps1' 'PSObject'
}
Test-Case 'Pin PSObject: same text in another function flagged' {
    Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Read-AgOther {', ' $p = Get-ItemProperty -Path x', ' foreach ($prop in $p.PSObject.Properties) { Write-Output 1 }', '}')) } 'lib\Common.ps1' 'PSObject'
}
Test-Case 'Pin PSObject: same text in another file flagged' { Flag-Files @{ 'other.ps1' = $psoGood } 'other.ps1' 'PSObject' }

# scope-prefix bypass (r3 script:, r7 global:, r4 MockFile): writes through a scope-qualified name
$probesBase = '$probes = [ordered]@{ host = { Write-Output 1 } }'
foreach ($sp in @('$script:probes', '$global:probes', '$local:probes', '${script:probes}', '$script:probes[''host'']')) {
    Test-Case "Scope bypass: $sp written before & `$probes[`$key] flagged" {
        Flag-Files @{ 'collector.ps1' = (Lines @($probesBase, "$sp = @{ host = 'calc.exe' }", 'foreach ($key in $probes.Keys) {', ' & $probes[$key]', '}')) } 'collector.ps1' 'dynamic'
    }
}
foreach ($sp in @('$script:MockFile', '$global:MockFile', '${global:MockFile}')) {
    Test-Case "Scope bypass: $sp written before the mock dot-source flagged" {
        Flag-Files @{ 'collector.ps1' = (Lines @('param([string]$MockFile)', "$sp = 'C:\x\evil.ps1'", $mockLine)) } 'collector.ps1' 'dynamic'
    }
}
foreach ($sp in @('$script:Body', '$global:Body')) {
    Test-Case "Scope bypass: $sp inside Invoke-Probe flagged" {
        Flag-Files @{ 'lib\Common.ps1' = (Lines @('function Invoke-Probe {', ' param([scriptblock]$Body)', " $sp = 'notepad.exe'", ' $d = & $Body', '}')) } 'lib\Common.ps1' 'dynamic'
    }
}
foreach ($sp in @('$script:x = 1', '$global:x = 1', '$local:x += 1', '${private:x} = 1', '$script:x++', 'foreach ($script:i in 1, 2) { Write-Output 1 }')) {
    Test-Case "Scope-qualified write flagged anywhere: $sp" { Flag-Case $sp 'scope' }
}
Test-Case 'Scope-qualified read is fine' { Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = "`$y = `$script:x`r`n" }) }

# $probes aliasing (a1, a2, a5) and every other appearance outside its three pinned sites
$pHead = '$probes = [ordered]@{ host = { Write-Output 1 } }'
$pLoop = @('foreach ($key in $probes.Keys) {', ' & $probes[$key]', '}')
$aliasCases = [ordered]@{
    'a1 alias then element write' = @($pHead, '$t = $probes', '$t[''host''] = ''calc.exe''') + $pLoop
    'a2 foreach over @($probes)'  = @($pHead, 'foreach ($t in @($probes)) { $t.host = ''calc.exe'' }') + $pLoop
    'a5 pipeline from @($probes)' = @($pHead, '@($probes) | ForEach-Object { $_[''host''] = ''calc.exe'' }') + $pLoop
    '$probes as an argument'      = @($pHead, 'Write-Output $probes') + $pLoop
    '$probes.Keys in a second foreach' = @($pHead) + $pLoop + @('foreach ($key in $probes.Keys) { Write-Output 1 }')
    'second call outside the foreach'  = @($pHead) + $pLoop + @('& $probes[$key]')
    '$probes read bare'           = @($pHead, '$probes') + $pLoop
    '$probes.Count read'          = @($pHead, '$n = $probes.Count') + $pLoop
}
foreach ($k in $aliasCases.Keys) {
    Test-Case "Probes pin: $k flagged" { Flag-Files @{ 'collector.ps1' = (Lines $aliasCases[$k]) } 'collector.ps1' 'probes' }
}
Test-Case 'Probes pin: $key assigned inside the foreach flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines @($pHead, 'foreach ($key in $probes.Keys) {', ' $key = ''x''', ' & $probes[$key]', '}')) } 'collector.ps1' 'dynamic'
}
Test-Case 'Probes pin: $key assigned before the foreach flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines (@($pHead, '$key = ''x''') + $pLoop)) } 'collector.ps1' 'dynamic'
}
Test-Case 'Probes pin: $probes in a lib file function flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines (@($pHead) + $pLoop)); 'lib\Common.ps1' = (Lines @('function Read-AgX { $probes.Keys }')) } 'lib\Common.ps1' 'probes'
}
Test-Case 'Probes pin: $probes in a probes\ file flagged' {
    Flag-Files @{ 'collector.ps1' = (Lines (@($pHead) + $pLoop)); 'probes\Host.ps1' = (Lines @('function Get-AgHost { $probes }')) } 'probes\Host.ps1' 'probes'
}
Test-Case 'Probes pin: exact three sites pass' { Assert-Passes (Invoke-GuardOn @{ 'collector.ps1' = (Lines (@($pHead) + $pLoop)) }) }

# provider-drive bypass: run-time built paths (v1, v2) and writes through command results
Test-Case 'v1 (Get-ChildItem (built Variable: path)).Value[x] = flagged' {
    Flag-Case "(Get-ChildItem ('Variable' + ':\probes')).Value['host'] = 'calc.exe'" 'constant'
}
Test-Case 'v2 $v = Get-ChildItem (built path); $v.Value = flagged (path)' {
    Flag-Files @{ 'probes\Host.ps1' = (Lines @('function Get-AgHost {', " `$v = Get-ChildItem -Path ('Variable'+':\probes')", ' $v.Value = [ordered]@{ host = ''calc.exe'' }', '}')); 'collector.ps1' = (Lines @('# h')) } 'probes\Host.ps1' 'constant'
}
Test-Case 'v2 $v = Get-ChildItem (built path); $v.Value = flagged (write)' {
    Flag-Files @{ 'probes\Host.ps1' = (Lines @('function Get-AgHost {', " `$v = Get-ChildItem -Path ('Variable'+':\probes')", ' $v.Value = [ordered]@{ host = ''calc.exe'' }', '}')); 'collector.ps1' = (Lines @('# h')) } 'probes\Host.ps1' 'command result'
}
Test-Case 'v2 style on $MockFile flagged' {
    Flag-Files @{ 'probes\Host.ps1' = (Lines @('function Get-AgHost {', " `$v = Get-ChildItem -Path ('Variable' + ':\MockFile')", ' $v.Value = ''C:\x\evil.ps1''', '}')) } 'probes\Host.ps1' 'constant'
}
foreach ($cmd in @('Get-ChildItem', 'Get-ItemProperty', 'Test-Path', 'Resolve-Path')) {
    Test-Case "Concatenated path flagged: $cmd" { Flag-Case "$cmd ('Variable' + ':\probes')" 'constant' }
    Test-Case "Positional undefined variable path flagged: $cmd" { Flag-Case "$cmd `$notconst" 'constant' }
    Test-Case "-LiteralPath with a subexpression flagged: $cmd" { Flag-Case "$cmd -LiteralPath `"`$(Get-Random)\x`"" 'constant' }
}
Test-Case '-f built path flagged' { Flag-Case "Get-ChildItem -Path ('{0}:\probes' -f 'Variable')" 'constant' }
Test-Case 'Path through a variable assigned from concatenation flagged' {
    Flag-Files @{ 'bad.ps1' = (Lines @('# h', '$d = ''Variable'' + '':\probes''', 'Get-ChildItem -Path $d')) } 'bad.ps1' 'constant'
}
Test-Case 'Path through a variable with one constant and one built assignment flagged' {
    Flag-Files @{ 'bad.ps1' = (Lines @('$d = ''HKLM:\a''', '$d = ''Variable'' + '':\probes''', 'Get-ChildItem -Path $d')) } 'bad.ps1' 'constant'
}
Test-Case 'Path with extra subexpression after $PSScriptRoot flagged' { Flag-Case 'Get-ChildItem "$PSScriptRoot\$x"' 'constant' }
Test-Case 'Pipeline input to a path cmdlet flagged' { Flag-Case '$x | Test-Path' 'constant' }
Test-Case 'Resolve-Path $MockFile outside collector.ps1 flagged' { Flag-Case 'Resolve-Path $MockFile' 'constant' }
foreach ($d in @('Env:', 'Function:', 'Alias:', 'Variable:\probes', 'Cert:\CurrentUser', 'WSMan:\localhost', 'Microsoft.PowerShell.Core\Variable::probes')) {
    Test-Case "Provider drive literal flagged: $d" { Flag-Case "Get-ChildItem $d" 'path' }
}
Test-Case 'Write through (Get-Service).StartType flagged' { Flag-Case "(Get-Service x).StartType = 'Disabled'" 'command result' }
Test-Case 'Write through $s = Get-Service; $s.Status flagged' {
    Flag-Files @{ 'bad.ps1' = (Lines @('# h', '$s = Get-Service x', '$s.Status = ''Stopped''')) } 'bad.ps1' 'command result'
}
Test-Case 'Write through $_ in a pipeline flagged' { Flag-Case "Get-Service | ForEach-Object { `$_.Status = 'x' }" 'command result' }
Test-Case 'Write through a foreach variable over a command flagged' {
    Flag-Files @{ 'bad.ps1' = (Lines @('# h', 'Write-Output 1', 'foreach ($s in (Get-Service)) { $s.Status = ''x'' }')) } 'bad.ps1' 'command result'
}
Test-Case 'Path positives pass' {
    Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = (Lines @(
        'Get-ItemProperty ''HKLM:\SOFTWARE\x'' -ErrorAction SilentlyContinue',
        'Get-ChildItem "$PSScriptRoot\probes\*.ps1"',
        'Test-Path "$env:LOCALAPPDATA\Microsoft\x.xml"',
        '$d = ''HKLM:\a''', 'Get-ItemProperty -Path $d -Name Foo',
        '$roots = @(''HKLM:\a'', ''HKCU:\b'')', 'foreach ($r in $roots) { Get-ItemProperty -Path $r }',
        'foreach ($p in @(''HKLM:\a'', ''HKLM:\b'')) { Get-ItemProperty -Path $p }',
        'Test-Path -PathType Leaf -LiteralPath ''HKLM:\z''')) })
}
Test-Case 'Writes to hashtable and ordered literals pass' {
    Assert-Passes (Invoke-GuardOn @{ 'a.ps1' = (Lines @('$h = [ordered]@{ a = 1 }', '$h[''b''] = 2', '$h.c = 3', '$t = @{}', '$t.x = Get-Random')) })
}
Test-Case 'MockFile path cmdlets in collector.ps1 with a parameter pass' {
    Assert-Passes (Invoke-GuardOn @{ 'collector.ps1' = (Lines @('param([string]$MockFile)', 'if ($MockFile -and -not (Test-Path -LiteralPath $MockFile)) { Write-Output 1 }')) })
}

# the pending-probe list must shrink as probes are written
Test-Case 'No name in $AgPendingProbes is defined in the real collector' {
    Assert-Run
    $txt = [IO.File]::ReadAllText($guard)
    $m = [regex]::Match($txt, '(?s)\$AgPendingProbes\s*=\s*@\((.*?)\)')
    Assert-True $m.Success 'AgPendingProbes list not found'
    $names = @([regex]::Matches($m.Groups[1].Value, "'([^']+)'") | ForEach-Object { $_.Groups[1].Value })
    Assert-True ($names.Count -gt 0) 'AgPendingProbes is empty (delete the list and this test)'
    foreach ($f in @(Get-ChildItem -LiteralPath $collRoot -Recurse -File -Filter *.ps1)) {
        $rel = $f.FullName.Substring($collRoot.Length).TrimStart('\')
        if ($rel -match '^(tests|mocks)\\') { continue }
        $body = [IO.File]::ReadAllText($f.FullName)
        foreach ($n in $names) {
            if ($body -match ('(?im)^\s*function\s+' + [regex]::Escape($n) + '\b')) { throw "$n is now defined in $rel; remove it from AgPendingProbes" }
        }
    }
}

Write-Output "Passed: $script:passed  Failed: $script:failed"
if ($script:failed -gt 0) { exit 1 } else { exit 0 }
