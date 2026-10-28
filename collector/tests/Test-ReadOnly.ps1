using namespace System.Management.Automation.Language
# collector/tests/Test-ReadOnly.ps1 - static AST guard for the read-only guarantee (manual 3.7).
# A strict superset of the manual's 3.7 snippet. Everything is an allowlist: commands, types, methods, cmdlet
# arguments and dynamic call sites must be listed or pinned below; anything else is a violation.
# Output is relative paths only (no absolute paths, no user names); names containing \ / : print as <redacted>.
param([string]$Root = (Join-Path $PSScriptRoot '..'), [switch]$NoRun)    # -NoRun: only define Invoke-AgReadOnlyScan (used by Test-ReadOnlyGuard.ps1)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\lib\Allowlist.ps1')     # the real allowlist, never one found under -Root

# =====================================================================================================
# Review required (Tshedi), same as Allowlist.ps1. Every list and pin that widens what the collector
# may do lives in this block.
# =====================================================================================================

# Type literals allowed anywhere (lower-case, without "System." prefix, without []).
$AgAllowedTypes = @(
    'console', 'diagnostics.stopwatch', 'datetime', 'globalization.cultureinfo', 'regex', 'text.regularexpressions.regexoptions',
    'string', 'io.path', 'security.principal.windowsprincipal', 'security.principal.windowsidentity',
    'security.principal.windowsbuiltinrole', 'argumentexception', 'security.cryptography.sha256', 'text.encoding',
    'io.file', 'ordered', 'int', 'bool', 'exception', 'collections.specialized.ordereddictionary',
    'management.managementdatetimeconverter'   # Phase 4: Recovery.ps1, converts a WMI restore-point time string (pure parsing)
)
# Extra types allowed only as a parameter type constraint (never as a cast or :: target).
$AgParamTypes = @('switch', 'scriptblock')

# Instance methods that may be called (on anything). Every other method call is a violation.
$AgAllowedMethods = @(
    'WriteLine', 'ToString', 'ToTitleCase', 'TrimEnd', 'Substring', 'IsInRole', 'ToUniversalTime', 'ComputeHash',
    'GetBytes', 'Dispose', 'GetUnresolvedProviderPathFromPSPath', 'NameSpace', 'ExtendedProperty'
)
# Static methods that may be called, as type.method (lower-case). Own classes may call ::new.
$AgAllowedStaticMethods = @(
    'diagnostics.stopwatch.startnew', 'regex.replace', 'regex.escape', 'io.path.getfilename',
    'security.principal.windowsidentity.getcurrent', 'security.cryptography.sha256.create', 'string.isnullorempty',
    'argumentexception.new', 'io.file.writealltext',
    'datetime.fromfiletimeutc',                         # Phase 4: Backup.ps1, File History ProtectedUpToTime (pure conversion)
    'management.managementdatetimeconverter.todatetime'   # Phase 4: Recovery.ps1, restore-point CreationTime (pure parsing)
)
# Property/method names that give reflection or provider access; flagged wherever they appear.
$AgReflectiveProps = @('Assembly', 'ImplementingType', 'InvokeProvider', 'InvokeCommand', 'Module', 'ScriptBlock', 'PSObject',
    'Methods', 'DeclaringType', 'UnderlyingSystemType', 'BaseType')
$AgBadVariables = @('Host', 'PSCmdlet')
$AgExecChain = '$ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)'   # only in Write-ScanJson, lib\Common.ps1
# The one allowed PSObject use: `foreach (... in $p.PSObject.Properties)` inside Read-AgAsrRegistry in lib\Common.ps1.
# It lists the value names (ASR rule GUIDs) under the ASR policy key; the set of GUIDs is not known ahead of time.
# Any other PSObject member, any other place, and any other use of this text stays flagged.
$AgPsObjectChain = '$p.PSObject.Properties'
$AgPsObjectFunction = 'Read-AgAsrRegistry'

# Parameters flagged on any command (also when abbreviated), and output-variable parameters.
$AgBadParams = @('ComputerName', 'CimSession', 'Session', 'Query', 'Credential')
$AgBadOutParams = @('OutVariable', 'OutBuffer', 'ErrorVariable', 'WarningVariable', 'InformationVariable', 'PipelineVariable', 'ov', 'ob', 'ev', 'wv', 'iv', 'pv')
$AgCimClasses = @('Win32_OperatingSystem', 'Win32_ShadowCopy', 'AntiVirusProduct')
$AgCimNamespaces = @('root/cimv2', 'root\cimv2', 'root/SecurityCenter2', 'root\SecurityCenter2')
$AgBadPathPattern = '^\s*(\\\\|(WSMan|Cert|Function|Variable|Alias|Env):|Microsoft\.PowerShell\.\w+\\)'   # UNC, provider drives, provider-qualified paths

$AgBadVerbs = @('Set', 'New', 'Remove', 'Add', 'Clear', 'Enable', 'Disable', 'Start', 'Stop', 'Restart', 'Suspend', 'Resume',
    'Install', 'Uninstall', 'Update', 'Register', 'Unregister')
$AgForbiddenLiteral = 'Win32_Product|vssadmin|wbadmin\s+start|manage-bde|bcdedit|Checkpoint-Computer|reagentc(\.exe)?\W+/(enable|disable)|-EncodedCommand|-WindowStyle\s+Hidden|\brunas\b'
$AgSingleDefinition = @('Write-ScanJson', 'Invoke-Probe')    # defined once, only in $AgCommonFile
$AgCommonFile = 'lib\Common.ps1'

# Pinned dynamic call sites (exact command text, whitespace-normalised). Each also has meaning checks in Test-DynamicPin.
$AgPinCommon = '. "$PSScriptRoot\lib\Common.ps1"'
$AgPinMock   = '. ([string](Resolve-Path $MockFile))'
$AgPinLoader = '. $_.FullName'
$AgPinLoaderSource = 'Get-ChildItem "$PSScriptRoot\probes\*.ps1"'
$AgPinProbes = '& $probes[$key]'
$AgPinBody   = '& $Body'
$AgReagentcFirst = '"$env:SystemRoot\System32\reagentc.exe"'   # pinned in a Read-Ag* function of $AgCommonFile, args /info [2>&1]

# =====================================================================================================

$script:violations = New-Object 'System.Collections.Generic.List[string]'
function Write-Violation([string]$Rel, [int]$Line, [string]$Msg) { $script:violations.Add(('{0}:{1} {2}' -f $Rel, $Line, $Msg)) }
function Get-SafeName([string]$Name) { if ($Name -match '[\\/:]') { return '<redacted>' } else { return $Name } }
function Get-TypeKey([string]$Name) {
    $n = ($Name -replace '\[.*$', '').Trim().ToLowerInvariant()
    if ($n.StartsWith('system.')) { $n = $n.Substring(7) }
    return $n
}
# Variable name without a leading scope qualifier (global:, script:, local:, private:, using:).
function Get-VarBase($VarAst) { return ($VarAst.VariablePath.UserPath -replace '^(?i)(global|script|local|private|using):', '') }
function Test-ScopeQualified($VarAst) { return ($VarAst.VariablePath.UserPath -match '^(?i)(global|script|local|private|using):') }
function Get-NormText($Node) { return ($Node.Extent.Text -replace '\s+', ' ').Trim() }
function Get-EnclosingFunctionName($Node) {
    $p = $Node.Parent
    while ($null -ne $p) {
        if ($p -is [FunctionDefinitionAst]) { return $p.Name }
        $p = $p.Parent
    }
    return $null
}
function Test-TopLevel($Node) {
    $p = $Node.Parent
    while ($null -ne $p) {
        if ($p -is [FunctionDefinitionAst] -or $p -is [ScriptBlockExpressionAst] -or $p -is [FunctionMemberAst]) { return $false }
        $p = $p.Parent
    }
    return $true
}
function Get-LineOf([string]$Text, [int]$Index) {
    $n = 1
    for ($i = 0; $i -lt $Index; $i++) { if ($Text[$i] -eq "`n") { $n++ } }
    return $n
}
# Every variable written inside $Scope: assignments (any variable on the left), foreach variables, ++/--.
function Get-WrittenVars($Scope) {
    $out = @()
    foreach ($a in $Scope.FindAll({ $args[0] -is [AssignmentStatementAst] }, $true)) {
        foreach ($v in $a.Left.FindAll({ $args[0] -is [VariableExpressionAst] }, $true)) { $out += [pscustomobject]@{ Var = $v; Stmt = $a } }
    }
    foreach ($f in $Scope.FindAll({ $args[0] -is [ForEachStatementAst] }, $true)) { $out += [pscustomobject]@{ Var = $f.Variable; Stmt = $f } }
    foreach ($u in $Scope.FindAll({ $args[0] -is [UnaryExpressionAst] }, $true)) {
        if ($u.TokenKind -in @('PlusPlus', 'MinusMinus', 'PostfixPlusPlus', 'PostfixMinusMinus')) {
            foreach ($v in $u.Child.FindAll({ $args[0] -is [VariableExpressionAst] }, $true)) { $out += [pscustomobject]@{ Var = $v; Stmt = $u } }
        }
    }
    return $out
}
function Test-ReagentcArgs($Cmd) {
    # exactly: <exe> /info [2>&1]
    if ($Cmd.CommandElements.Count -ne 2) { return $false }
    $a = $Cmd.CommandElements[1]
    if (-not ($a -is [StringConstantExpressionAst]) -or $a.StringConstantType -ne 'BareWord' -or $a.Value -ine '/info') { return $false }
    if ($Cmd.Redirections.Count -gt 1) { return $false }
    foreach ($r in $Cmd.Redirections) {
        if (-not ($r -is [MergingRedirectionAst]) -or $r.FromStream -ne 'Error' -or $r.ToStream -ne 'Output') { return $false }
    }
    return $true
}
function Get-StatementExpr($S) {
    if ($S -is [CommandExpressionAst]) { return $S.Expression }
    if ($S -is [PipelineAst] -and $S.PipelineElements.Count -eq 1 -and $S.PipelineElements[0] -is [CommandExpressionAst]) { return $S.PipelineElements[0].Expression }
    return $null
}
function Test-ScriptBlockLiteralTable($Assign) {
    # right side is @{...} or [ordered]@{...} whose values are all scriptblock literals
    $e = Get-StatementExpr $Assign.Right
    if ($e -is [ConvertExpressionAst]) {
        if ((Get-TypeKey $e.Type.TypeName.FullName) -ne 'ordered') { return $false }
        $e = $e.Child
    }
    if (-not ($e -is [HashtableAst]) -or $e.KeyValuePairs.Count -eq 0) { return $false }
    foreach ($kv in $e.KeyValuePairs) {
        if (-not ((Get-StatementExpr $kv.Item2) -is [ScriptBlockExpressionAst])) { return $false }
    }
    return $true
}
function Test-CimArgs($Cmd) {
    $e = @($Cmd.CommandElements | Select-Object -Skip 1)
    $i = 0; $class = $null
    while ($i -lt $e.Count) {
        $x = $e[$i]
        if (-not ($x -is [CommandParameterAst])) { return $false }
        $val = $x.Argument
        if ($null -eq $val) { $i++; if ($i -ge $e.Count) { return $false }; $val = $e[$i] }
        if (-not ($val -is [StringConstantExpressionAst])) { return $false }
        if ($x.ParameterName -ieq 'ClassName') { if ($AgCimClasses -notcontains $val.Value) { return $false }; $class = $val.Value }
        elseif ($x.ParameterName -ieq 'Namespace') { if ($AgCimNamespaces -notcontains $val.Value) { return $false } }
        elseif ($x.ParameterName -ieq 'ErrorAction') { }
        else { return $false }
        $i++
    }
    return ($null -ne $class)
}
# Meaning checks for a dynamic (&, .) call site; $FileAst is the whole file.
function Test-DynamicPin($C, [string]$Rel, $FileAst) {
    $text = Get-NormText $C
    $isCollector = ($Rel -ieq 'collector.ps1')
    if ($text -ceq $AgPinCommon) { return ($isCollector -and (Test-TopLevel $C)) }
    if ($text -ceq $AgPinMock) {
        if (-not ($isCollector -and (Test-TopLevel $C))) { return $false }
        if ($null -eq $FileAst.ParamBlock) { return $false }
        $isParam = $false
        foreach ($pa in $FileAst.ParamBlock.Parameters) { if ((Get-VarBase $pa.Name) -ieq 'MockFile') { $isParam = $true } }
        if (-not $isParam) { return $false }
        foreach ($w in @(Get-WrittenVars $FileAst)) { if ((Get-VarBase $w.Var) -ieq 'MockFile') { return $false } }
        return $true
    }
    if ($text -ceq $AgPinProbes) {
        if (-not ($isCollector -and (Test-TopLevel $C))) { return $false }
        if (-not (Test-ProbesLoop (Get-NearestForEach $C) $Rel $FileAst)) { return $false }
        $w = @(Get-WrittenVars $FileAst | Where-Object { (Get-VarBase $_.Var) -ieq 'probes' })
        if ($w.Count -ne 1) { return $false }
        $stmt = $w[0].Stmt
        if (-not ($stmt -is [AssignmentStatementAst]) -or -not ($stmt.Left -is [VariableExpressionAst])) { return $false }
        return (Test-ScriptBlockLiteralTable $stmt)
    }
    if ($text -ceq $AgPinLoader) {
        if (-not $isCollector) { return $false }
        $sb = $C.Parent
        while ($null -ne $sb -and -not ($sb -is [ScriptBlockExpressionAst])) { $sb = $sb.Parent }
        if ($null -eq $sb) { return $false }
        $fe = $sb.Parent
        if (-not ($fe -is [CommandAst]) -or $fe.GetCommandName() -ine 'ForEach-Object') { return $false }
        $pl = $fe.Parent
        if (-not ($pl -is [PipelineAst]) -or $pl.PipelineElements.Count -ne 2 -or -not [object]::ReferenceEquals($pl.PipelineElements[1], $fe)) { return $false }
        return ((Get-NormText $pl.PipelineElements[0]) -ceq $AgPinLoaderSource)
    }
    if ($text -ceq $AgPinBody) {
        if ($Rel -ine $AgCommonFile) { return $false }
        $fn = $C.Parent
        while ($null -ne $fn -and -not ($fn -is [FunctionDefinitionAst])) { $fn = $fn.Parent }
        if ($null -eq $fn -or $fn.Name -ine 'Invoke-Probe') { return $false }
        $params = @($fn.FindAll({ $args[0] -is [ParameterAst] }, $true) | Where-Object { (Get-VarBase $_.Name) -ieq 'Body' })
        if ($params.Count -ne 1) { return $false }
        $typed = $false
        foreach ($at in $params[0].Attributes) { if ($at -is [TypeConstraintAst] -and (Get-TypeKey $at.TypeName.FullName) -eq 'scriptblock') { $typed = $true } }
        if (-not $typed) { return $false }
        foreach ($w in @(Get-WrittenVars $fn)) { if ((Get-VarBase $w.Var) -ieq 'Body') { return $false } }
        return $true
    }
    # reagentc.exe, full path, pinned to a Read-Ag* function in the Common file
    if ($Rel -ieq $AgCommonFile -and $C.CommandElements[0].Extent.Text -ceq $AgReagentcFirst -and (Test-ReagentcArgs $C)) {
        return ((Get-EnclosingFunctionName $C) -like 'Read-Ag*')
    }
    return $false
}
function Test-PsObjectPin($M, [string]$Rel) {
    if ($Rel -ine $AgCommonFile -or (Get-EnclosingFunctionName $M) -ine $AgPsObjectFunction) { return $false }
    $top = $M.Parent
    if (-not ($top -is [MemberExpressionAst]) -or $top -is [InvokeMemberExpressionAst] -or -not [object]::ReferenceEquals($top.Expression, $M)) { return $false }
    if ((Get-NormText $top) -cne $AgPsObjectChain) { return $false }
    $fe = $top.Parent
    while ($null -ne $fe -and -not ($fe -is [ForEachStatementAst])) { $fe = $fe.Parent }
    if ($null -eq $fe) { return $false }
    # the chain must be the foreach collection itself, not something in its body
    return ($fe.Condition.Extent.StartOffset -eq $top.Extent.StartOffset -and $fe.Condition.Extent.EndOffset -eq $top.Extent.EndOffset)
}
# The one top-level `foreach ($key in $probes.Keys)` of collector.ps1; $key is written nowhere else in the file.
function Test-ProbesLoop($F, [string]$Rel, $FileAst) {
    if (-not ($F -is [ForEachStatementAst]) -or $Rel -ine 'collector.ps1' -or -not (Test-TopLevel $F)) { return $false }
    if ((Get-VarBase $F.Variable) -ine 'key') { return $false }
    if ((Get-NormText $F.Condition) -cne '$probes.Keys') { return $false }
    # `$scan[$key] = ...` only reads $key (it is the index), so index positions do not count as writes
    $kw = @(Get-WrittenVars $FileAst | Where-Object {
        (Get-VarBase $_.Var) -ieq 'key' -and -not ($_.Var.Parent -is [IndexExpressionAst] -and [object]::ReferenceEquals($_.Var.Parent.Index, $_.Var))
    })
    return ($kw.Count -eq 1 -and [object]::ReferenceEquals($kw[0].Stmt, $F))
}
function Get-NearestForEach($Node) {
    $p = $Node.Parent
    while ($null -ne $p -and -not ($p -is [ForEachStatementAst])) { $p = $p.Parent }
    return $p
}
# 1 = the single assignment, 2 = $probes.Keys as the foreach collection, 3 = $probes[$key] of the pinned call, 0 = anything else.
function Get-ProbesSiteType($V, [string]$Rel, $FileAst) {
    if ($Rel -ine 'collector.ps1') { return 0 }
    $par = $V.Parent
    if ($par -is [AssignmentStatementAst] -and [object]::ReferenceEquals($par.Left, $V)) {
        if ((Test-TopLevel $par) -and (Test-ScriptBlockLiteralTable $par)) { return 1 }
        return 0
    }
    if ($par -is [MemberExpressionAst] -and -not ($par -is [InvokeMemberExpressionAst]) -and [object]::ReferenceEquals($par.Expression, $V) -and
        $par.Member -is [StringConstantExpressionAst] -and $par.Member.Value -ceq 'Keys') {
        $f = Get-NearestForEach $par
        if ($null -ne $f -and $f.Condition.Extent.StartOffset -eq $par.Extent.StartOffset -and $f.Condition.Extent.EndOffset -eq $par.Extent.EndOffset -and
            (Test-ProbesLoop $f $Rel $FileAst)) { return 2 }
        return 0
    }
    if ($par -is [IndexExpressionAst] -and [object]::ReferenceEquals($par.Target, $V) -and $par.Index -is [VariableExpressionAst] -and (Get-VarBase $par.Index) -ieq 'key') {
        $c = $par.Parent
        if ($c -is [CommandAst] -and $c.CommandElements.Count -eq 1 -and [object]::ReferenceEquals($c.CommandElements[0], $par) -and
            $c.InvocationOperator -eq 'Ampersand') {
            $f = Get-NearestForEach $c
            if (Test-ProbesLoop $f $Rel $FileAst) { return 3 }
        }
    }
    return 0
}
# ---- variable tracking, per function scope ('TOP' = script level of any scanned file) ----
$script:VarSrc = @{}        # 'scope|name' -> list of @{Expr; Rel}; Expr $null = not a constant source
$script:CmdVar = @{}        # 'scope|name' -> $true when assigned from a command result
$script:FuncAssigned = @{}  # name -> $true when assigned inside any function
function Get-ScopeKey($Node, [string]$Rel) {
    $p = $Node.Parent
    while ($null -ne $p) {
        if ($p -is [FunctionDefinitionAst] -or $p -is [FunctionMemberAst]) { return ($Rel + ':' + $p.Extent.StartOffset) }
        $p = $p.Parent
    }
    return 'TOP'
}
function Test-CommandDerived($N, [string]$Rel) {
    if ($null -eq $N) { return $false }
    if ($N -is [PipelineAst]) {
        foreach ($el in $N.PipelineElements) {
            if ($el -is [CommandAst]) { return $true }
            if ($el -is [CommandExpressionAst] -and (Test-CommandDerived $el.Expression $Rel)) { return $true }
        }
        return $false
    }
    if ($N -is [CommandExpressionAst]) { return (Test-CommandDerived $N.Expression $Rel) }
    if ($N -is [ParenExpressionAst]) { return (Test-CommandDerived $N.Pipeline $Rel) }
    if ($N -is [SubExpressionAst] -or $N -is [ArrayExpressionAst]) {
        foreach ($st in $N.SubExpression.Statements) { if (Test-CommandDerived $st $Rel) { return $true } }
        return $false
    }
    if ($N -is [ConvertExpressionAst]) { return (Test-CommandDerived $N.Child $Rel) }
    if ($N -is [MemberExpressionAst]) { return (Test-CommandDerived $N.Expression $Rel) }
    if ($N -is [IndexExpressionAst]) { return (Test-CommandDerived $N.Target $Rel) }
    if ($N -is [BinaryExpressionAst]) { return ((Test-CommandDerived $N.Left $Rel) -or (Test-CommandDerived $N.Right $Rel)) }
    if ($N -is [ArrayLiteralAst]) {
        foreach ($el in $N.Elements) { if (Test-CommandDerived $el $Rel) { return $true } }
        return $false
    }
    if ($N -is [VariableExpressionAst]) { return (Test-CmdVar $N $Rel) }
    if ($N -is [HashtableAst] -or $N -is [ConstantExpressionAst] -or $N -is [StringConstantExpressionAst] -or $N -is [ExpandableStringExpressionAst]) { return $false }
    if ($N -is [StatementAst]) { return ($N.FindAll({ $args[0] -is [CommandAst] }, $true).Count -gt 0) }
    return $false
}
function Test-CmdVar($V, [string]$Rel) {
    $name = (Get-VarBase $V).ToLowerInvariant()
    return ($script:CmdVar.ContainsKey((Get-ScopeKey $V $Rel) + '|' + $name) -or $script:CmdVar.ContainsKey('TOP|' + $name))
}
function Register-VarWrite($Node, [string]$Rel, $VarAst, $Expr, [bool]$Cmd) {
    $scope = Get-ScopeKey $Node $Rel
    $name = (Get-VarBase $VarAst).ToLowerInvariant()
    $k = $scope + '|' + $name
    if (-not $script:VarSrc.ContainsKey($k)) { $script:VarSrc[$k] = New-Object System.Collections.ArrayList }
    [void]$script:VarSrc[$k].Add([pscustomobject]@{ Expr = $Expr; Rel = $Rel })
    if ($Cmd) { $script:CmdVar[$k] = $true }
    if ($scope -ne 'TOP') { $script:FuncAssigned[$name] = $true }
}
function Register-FileVars($Ast, [string]$Rel) {
    foreach ($a in $Ast.FindAll({ $args[0] -is [AssignmentStatementAst] }, $true)) {
        $plain = ($a.Left -is [VariableExpressionAst]) -and $a.Operator -eq 'Equals'
        $cmd = $plain -or ($a.Left -is [ArrayLiteralAst]) -or ($a.Operator -ne 'Equals' -and $a.Left -is [VariableExpressionAst])
        if ($cmd) { $cmd = Test-CommandDerived $a.Right $Rel }
        $src = $null
        if ($plain) { $src = Get-StatementExpr $a.Right }
        foreach ($v in $a.Left.FindAll({ $args[0] -is [VariableExpressionAst] }, $true)) {
            Register-VarWrite $a $Rel $v $src $cmd
        }
    }
    foreach ($f in $Ast.FindAll({ $args[0] -is [ForEachStatementAst] }, $true)) {
        Register-VarWrite $f $Rel $f.Variable (Get-StatementExpr $f.Condition) (Test-CommandDerived $f.Condition $Rel)
    }
    foreach ($u in $Ast.FindAll({ $args[0] -is [UnaryExpressionAst] }, $true)) {
        if ($u.TokenKind -in @('PlusPlus', 'MinusMinus', 'PostfixPlusPlus', 'PostfixMinusMinus')) {
            foreach ($v in $u.Child.FindAll({ $args[0] -is [VariableExpressionAst] }, $true)) { Register-VarWrite $u $Rel $v $null $false }
        }
    }
    foreach ($pa in $Ast.FindAll({ $args[0] -is [ParameterAst] }, $true)) { Register-VarWrite $pa $Rel $pa.Name $null $false }
}
# A path value is constant: string literal, "$PSScriptRoot..."/"$env:X..." with no other subexpression, a variable
# only ever assigned such values (or a foreach variable over such an array), or arrays of those.
function Test-ConstPath($E, [string]$Rel, $Visiting) {
    if ($null -eq $E) { return $false }
    if ($E -is [StringConstantExpressionAst]) { return $true }
    if ($E -is [ExpandableStringExpressionAst]) {
        if ($E.NestedExpressions.Count -ne 1) { return $false }
        $n = $E.NestedExpressions[0]
        if (-not ($n -is [VariableExpressionAst])) { return $false }
        $isRoot = (Get-VarBase $n) -ieq 'PSScriptRoot'
        $isEnv = $n.VariablePath.IsDriveQualified -and $n.VariablePath.DriveName -ieq 'env'
        return (($isRoot -or $isEnv) -and ($n.Extent.StartOffset - $E.Extent.StartOffset) -eq 1)
    }
    if ($E -is [ParenExpressionAst]) { return (Test-ConstPath (Get-StatementExpr $E.Pipeline) $Rel $Visiting) }
    if ($E -is [ArrayLiteralAst]) {
        foreach ($el in $E.Elements) { if (-not (Test-ConstPath $el $Rel $Visiting)) { return $false } }
        return $true
    }
    if ($E -is [ArrayExpressionAst]) {
        foreach ($st in $E.SubExpression.Statements) { if (-not (Test-ConstPath (Get-StatementExpr $st) $Rel $Visiting)) { return $false } }
        return $true
    }
    if ($E -is [VariableExpressionAst]) {
        $name = (Get-VarBase $E).ToLowerInvariant()
        if ($name -eq 'psscriptroot') { return $true }
        if ($E.VariablePath.IsDriveQualified -and $E.VariablePath.DriveName -ieq 'env') { return $true }
        $k = (Get-ScopeKey $E $Rel) + '|' + $name
        if (-not $script:VarSrc.ContainsKey($k)) {
            # free variable: only a script-level variable that no function assigns (functions see their callers' variables)
            if ($script:FuncAssigned.ContainsKey($name) -or -not $script:VarSrc.ContainsKey('TOP|' + $name)) { return $false }
            $k = 'TOP|' + $name
        }
        if ($Visiting.ContainsKey($k)) { return $false }
        $Visiting[$k] = $true
        $ok = $true
        foreach ($s in $script:VarSrc[$k]) { if (-not (Test-ConstPath $s.Expr $s.Rel $Visiting)) { $ok = $false; break } }
        $Visiting.Remove($k)
        return $ok
    }
    return $false
}
# The path values given to Get-ChildItem, Get-ItemProperty, Test-Path and Resolve-Path (named, abbreviated or positional).
function Get-PathArgs($C) {
    $valued = @('Name', 'Filter', 'Include', 'Exclude', 'Depth', 'ErrorAction', 'WarningAction', 'InformationAction', 'PathType', 'Attributes', 'Stream', 'OlderThan', 'NewerThan')
    $switches = @('Recurse', 'Force', 'File', 'Directory', 'Hidden', 'System', 'ReadOnly', 'Relative', 'FollowSymlink')
    $out = @()
    $e = @($C.CommandElements | Select-Object -Skip 1)
    $i = 0
    while ($i -lt $e.Count) {
        $x = $e[$i]
        if ($x -is [CommandParameterAst]) {
            $pn = $x.ParameterName
            $isPath = ('Path'.StartsWith($pn, [StringComparison]::OrdinalIgnoreCase) -or 'LiteralPath'.StartsWith($pn, [StringComparison]::OrdinalIgnoreCase) -or 'PSPath'.StartsWith($pn, [StringComparison]::OrdinalIgnoreCase))
            if ($null -ne $x.Argument) { if ($isPath) { $out += $x.Argument }; $i++; continue }
            $takes = $false
            if ($isPath) { $takes = $true }
            elseif ($valued | Where-Object { $_.StartsWith($pn, [StringComparison]::OrdinalIgnoreCase) }) { $takes = -not ($switches -contains $pn) }
            if ($takes -and ($i + 1) -lt $e.Count -and -not ($e[$i + 1] -is [CommandParameterAst])) {
                if ($isPath) { $out += $e[$i + 1] }
                $i += 2; continue
            }
            $i++; continue
        }
        $out += $x     # positional: treated as a path
        $i++
    }
    return $out
}
function Test-MockFileArg($E, [string]$Rel, $FileAst) {
    if (-not ($E -is [VariableExpressionAst]) -or (Get-VarBase $E) -ine 'MockFile' -or $Rel -ine 'collector.ps1') { return $false }
    if ($null -eq $FileAst.ParamBlock) { return $false }
    $isParam = $false
    foreach ($pa in $FileAst.ParamBlock.Parameters) { if ((Get-VarBase $pa.Name) -ieq 'MockFile') { $isParam = $true } }
    if (-not $isParam) { return $false }
    foreach ($w in @(Get-WrittenVars $FileAst)) { if ((Get-VarBase $w.Var) -ieq 'MockFile') { return $false } }
    return $true
}
function Test-ExecChain($V, [string]$Rel) {
    if ($Rel -ine $AgCommonFile -or (Get-EnclosingFunctionName $V) -ine 'Write-ScanJson') { return $false }
    $top = $V
    while ($top.Parent -is [MemberExpressionAst] -and [object]::ReferenceEquals($top.Parent.Expression, $top)) { $top = $top.Parent }
    return ((Get-NormText $top) -ceq $AgExecChain)
}

# ---- real-command lookup, batched and cached (one Get-Command per scan for names not seen before) ----
if ($null -eq $script:AgCmdCache) { $script:AgCmdCache = @{} }
function Initialize-AgCommandCache([string[]]$Names) {
    $todo = @($Names | Where-Object { -not $script:AgCmdCache.ContainsKey($_.ToLowerInvariant()) } | Sort-Object -Unique)
    if ($todo.Count -eq 0) { return }
    $plain = @($todo | Where-Object { $_ -notmatch '[\*\?\[\]]' })
    foreach ($w in @($todo | Where-Object { $_ -match '[\*\?\[\]]' })) {   # wildcard characters: look up on their own, as before
        $script:AgCmdCache[$w.ToLowerInvariant()] = [bool](Get-Command -Name $w -CommandType Cmdlet, Alias, Application -ErrorAction SilentlyContinue)
    }
    if ($plain.Count -eq 0) { return }
    $found = @{}
    foreach ($c in @(Get-Command -Name $plain -CommandType Cmdlet, Alias, Application -ErrorAction SilentlyContinue)) {
        $found[$c.Name.ToLowerInvariant()] = $true
        $found[[IO.Path]::GetFileNameWithoutExtension($c.Name).ToLowerInvariant()] = $true   # an Application is found by its name without .exe
    }
    foreach ($n in $plain) { $script:AgCmdCache[$n.ToLowerInvariant()] = $found.ContainsKey($n.ToLowerInvariant()) }
}
function Test-AgRealCommand([string]$Name) {
    $k = $Name.ToLowerInvariant()
    if (-not $script:AgCmdCache.ContainsKey($k)) { Initialize-AgCommandCache @($Name) }
    return $script:AgCmdCache[$k]
}

# Scans $Root and returns the violation lines (an empty array means READ-ONLY OK). Never writes output and never exits.
function Invoke-AgReadOnlyScan([string]$Root) {
    $script:violations = New-Object 'System.Collections.Generic.List[string]'
    $script:VarSrc = @{}; $script:CmdVar = @{}; $script:FuncAssigned = @{}
    if (-not [IO.Directory]::Exists($Root)) { return @('Root folder not found') }
    $rootFull = (Resolve-Path -LiteralPath $Root).ProviderPath.TrimEnd('\', '/') + '\'

    # collect files, excluding tests\ and mocks\ by path relative to Root
    $files = @()
    foreach ($f in @(Get-ChildItem -LiteralPath $rootFull -Recurse -Force -File -Filter *.ps1)) {
        if (-not $f.FullName.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) { continue }
        $rel = $f.FullName.Substring($rootFull.Length)
        $first = $rel.Split('\')[0]
        if ($rel.Contains('\') -and ($first -ieq 'tests' -or $first -ieq 'mocks')) { continue }
        $files += [pscustomobject]@{ Full = $f.FullName; Rel = $rel }
    }
    if ($files.Count -eq 0) { return @('no scripts found to check') }

    # parse everything; gather own functions (with locations) and own types
    $ownFunctions = @{}
    $defs = @{}
    $ownTypes = @{}
    $parsed = @()
    foreach ($f in $files) {
        $tokens = $null; $errs = $null
        $ast = [Parser]::ParseFile($f.Full, [ref]$tokens, [ref]$errs)
        foreach ($e in @($errs)) { Write-Violation $f.Rel $e.Extent.StartLineNumber ('parse error (' + $e.ErrorId + ')') }
        $parsed += [pscustomobject]@{ Rel = $f.Rel; Full = $f.Full; Ast = $ast }
        Register-FileVars $ast $f.Rel
        foreach ($fd in $ast.FindAll({ $args[0] -is [FunctionDefinitionAst] }, $true)) {
            $k = ($fd.Name -replace '^\w+:', '').ToLowerInvariant()
            $ownFunctions[$k] = $true
            if (-not $defs.ContainsKey($k)) { $defs[$k] = @() }
            $defs[$k] += [pscustomobject]@{ Rel = $f.Rel; Line = $fd.Extent.StartLineNumber; Name = ($fd.Name -replace '^\w+:', '') }
        }
        foreach ($td in $ast.FindAll({ $args[0] -is [TypeDefinitionAst] }, $true)) { $ownTypes[$td.Name.ToLowerInvariant()] = $true }
    }
    Initialize-AgCommandCache @($defs.Values | ForEach-Object { $_ } | ForEach-Object { $_.Name })   # one batched lookup for the whole scan
    # duplicate definitions; single-definition functions only in the Common file
    foreach ($k in $defs.Keys) {
        $list = @($defs[$k])
        if ($list.Count -gt 1) {
            foreach ($d in $list) { Write-Violation $d.Rel $d.Line ('function defined more than once: ' + (Get-SafeName $d.Name)) }
        }
        foreach ($d in $list) {
            if (($AgSingleDefinition -contains $d.Name) -and $d.Rel -ine $AgCommonFile) {
                Write-Violation $d.Rel $d.Line ('function may only be defined in ' + $AgCommonFile + ': ' + (Get-SafeName $d.Name))
            }
        }
    }

    foreach ($p in $parsed) {
        $rel = $p.Rel
        $ast = $p.Ast

        # #requires of any kind
        if ($null -ne $ast.ScriptRequirements) { Write-Violation $rel 1 '#requires not allowed' }

        # own function definitions must not use mutating verbs or shadow real commands
        foreach ($fd in $ast.FindAll({ $args[0] -is [FunctionDefinitionAst] }, $true)) {
            $n = $fd.Name -replace '^\w+:', ''
            $ln = $fd.Extent.StartLineNumber
            $verb = $n.Split('-')[0]
            if ($n.Contains('-') -and $AgBadVerbs -contains $verb) { Write-Violation $rel $ln ('function with forbidden verb defined: ' + (Get-SafeName $n)) }
            elseif ($n -ieq 'Invoke-WebRequest' -or $n -ieq 'Invoke-RestMethod') { Write-Violation $rel $ln ('function with forbidden name defined: ' + (Get-SafeName $n)) }
            elseif (Test-AgRealCommand $n) {
                Write-Violation $rel $ln ('function shadows a real command: ' + (Get-SafeName $n))
            }
        }

        # commands
        foreach ($c in $ast.FindAll({ $args[0] -is [CommandAst] }, $true)) {
            $ln = $c.Extent.StartLineNumber
            $name = $c.GetCommandName()
            if ($null -eq $name) {
                if (-not (Test-DynamicPin $c $rel $ast)) { Write-Violation $rel $ln 'dynamic command invocation not allowed' }
                continue
            }
            if ($name -ieq 'New-Object') {
                $a = @($c.CommandElements | Select-Object -Skip 1)
                $ok = $false
                if ($a.Count -eq 2 -and $a[0] -is [CommandParameterAst] -and $a[0].ParameterName -ieq 'ComObject' -and $null -eq $a[0].Argument -and
                    $a[1] -is [StringConstantExpressionAst] -and $a[1].Value -ieq 'Shell.Application') { $ok = $true }
                if (($a.Count -eq 1 -or $a.Count -eq 2) -and $a[0] -is [StringConstantExpressionAst] -and
                    ($a[0].Value -ieq 'Text.UTF8Encoding' -or $a[0].Value -ieq 'System.Text.UTF8Encoding')) {
                    if ($a.Count -eq 1) { $ok = $true }
                    elseif ($a[1] -is [VariableExpressionAst] -and (Get-VarBase $a[1]) -ieq 'false') { $ok = $true }
                }
                if (-not $ok) { Write-Violation $rel $ln 'New-Object arguments not allowed' }
                continue
            }
            if ($name -ieq 'reagentc.exe') { Write-Violation $rel $ln 'reagentc.exe only allowed as the pinned full-path /info call'; continue }
            if ($name -ieq 'ForEach-Object') {
                $a = @($c.CommandElements | Select-Object -Skip 1)
                if ($a.Count -ne 1 -or -not ($a[0] -is [ScriptBlockExpressionAst])) { Write-Violation $rel $ln 'ForEach-Object takes a scriptblock only' }
                continue
            }
            if ($name -ieq 'Get-CimInstance') {
                if (-not (Test-CimArgs $c)) { Write-Violation $rel $ln 'Get-CimInstance arguments not allowed' }
                continue
            }
            $key = ($name -replace '^\w+:', '').ToLowerInvariant()
            if ($AgAllowedCommands -contains $name) { continue }
            if ($ownFunctions.ContainsKey($key)) { continue }
            Write-Violation $rel $ln ('command not allowed: ' + (Get-SafeName $name))
        }

        # parameters on any command
        foreach ($pm in $ast.FindAll({ $args[0] -is [CommandParameterAst] }, $true)) {
            $pn = $pm.ParameterName
            foreach ($b in $AgBadParams) {
                if ($b.StartsWith($pn, [StringComparison]::OrdinalIgnoreCase)) { Write-Violation $rel $pm.Extent.StartLineNumber ('parameter not allowed: -' + $b); break }
            }
            if ($AgBadOutParams -contains $pn) { Write-Violation $rel $pm.Extent.StartLineNumber 'output-variable parameter not allowed' }
        }

        # type literals
        foreach ($t in $ast.FindAll({ $args[0] -is [TypeExpressionAst] }, $true)) {
            $k = Get-TypeKey $t.TypeName.FullName
            $ln = $t.Extent.StartLineNumber
            if ($k -eq 'io.file') {
                $m = $t.Parent
                $ok = ($m -is [InvokeMemberExpressionAst]) -and $m.Static -and [object]::ReferenceEquals($m.Expression, $t) -and
                    ($m.Member -is [StringConstantExpressionAst]) -and ($m.Member.Value -ieq 'WriteAllText') -and
                    ((Get-EnclosingFunctionName $t) -ieq 'Write-ScanJson')
                if (-not $ok) { Write-Violation $rel $ln ('[' + $t.TypeName.FullName + '] only allowed as WriteAllText inside Write-ScanJson') }
            } elseif (($AgAllowedTypes -notcontains $k) -and -not $ownTypes.ContainsKey($k)) {
                Write-Violation $rel $ln ('type not allowed: ' + (Get-SafeName $t.TypeName.FullName))
            }
        }
        foreach ($t in $ast.FindAll({ $args[0] -is [TypeConstraintAst] }, $true)) {
            $k = Get-TypeKey $t.TypeName.FullName
            if ($k -eq 'io.file') { Write-Violation $rel $t.Extent.StartLineNumber ('[' + $t.TypeName.FullName + '] not allowed as a constraint'); continue }
            $ok = ($AgAllowedTypes -contains $k) -or $ownTypes.ContainsKey($k) -or
                (($t.Parent -is [ParameterAst]) -and ($AgParamTypes -contains $k))
            if (-not $ok) { Write-Violation $rel $t.Extent.StartLineNumber ('type not allowed: ' + (Get-SafeName $t.TypeName.FullName)) }
        }
        foreach ($u in $ast.FindAll({ $args[0] -is [UsingStatementAst] }, $true)) {
            Write-Violation $rel $u.Extent.StartLineNumber 'using statement not allowed'
        }

        # members and methods
        foreach ($m in $ast.FindAll({ $args[0] -is [MemberExpressionAst] }, $true)) {
            $ln = $m.Extent.StartLineNumber
            if (-not ($m.Member -is [StringConstantExpressionAst])) { Write-Violation $rel $ln 'dynamic member name not allowed'; continue }
            $mn = $m.Member.Value
            $sn = Get-SafeName $mn
            if ($AgReflectiveProps -contains $mn -and -not ($mn -ieq 'PSObject' -and (Test-PsObjectPin $m $rel))) { Write-Violation $rel $ln ('member not allowed: ' + $sn) }
            if ($m.Static -and -not ($m.Expression -is [TypeExpressionAst])) { Write-Violation $rel $ln 'static member access needs a type literal'; continue }
            if ($m -is [InvokeMemberExpressionAst]) {
                if ($m.Static) {
                    $tk = Get-TypeKey $m.Expression.TypeName.FullName
                    $ok = ($AgAllowedStaticMethods -contains ($tk + '.' + $mn.ToLowerInvariant())) -or ($ownTypes.ContainsKey($tk) -and $mn -ieq 'new')
                    if (-not $ok) { Write-Violation $rel $ln ('static method not allowed: [' + (Get-SafeName $m.Expression.TypeName.FullName) + ']::' + $sn) }
                } elseif ($AgAllowedMethods -notcontains $mn) {
                    Write-Violation $rel $ln ('method not allowed: ' + $sn)
                }
            }
        }

        # path arguments of Get-ChildItem, Get-ItemProperty, Test-Path, Resolve-Path must be constant
        foreach ($c in $ast.FindAll({ $args[0] -is [CommandAst] }, $true)) {
            $cn = $c.GetCommandName()
            if ($null -eq $cn -or @('Get-ChildItem', 'Get-ItemProperty', 'Test-Path', 'Resolve-Path') -notcontains $cn) { continue }
            $bad = $false
            $pl = $c.Parent
            if ($pl -is [PipelineAst] -and $pl.PipelineElements.Count -gt 1 -and -not [object]::ReferenceEquals($pl.PipelineElements[0], $c)) { $bad = $true }
            foreach ($pa in @(Get-PathArgs $c)) {
                if (Test-MockFileArg $pa $rel $ast) { continue }
                if (-not (Test-ConstPath $pa $rel @{})) { $bad = $true }
            }
            if ($bad) { Write-Violation $rel $c.Extent.StartLineNumber 'path argument must be a constant' }
        }

        # writes through a command result: (cmd).X = ..., $_.X = ..., or a variable assigned from a command
        foreach ($a in $ast.FindAll({ $args[0] -is [AssignmentStatementAst] }, $true)) {
            if (-not ($a.Left -is [MemberExpressionAst] -or $a.Left -is [IndexExpressionAst])) { continue }
            $wr = $a.Left
            while ($true) {
                if ($wr -is [MemberExpressionAst]) { $wr = $wr.Expression }
                elseif ($wr -is [IndexExpressionAst]) { $wr = $wr.Target }
                elseif ($wr -is [ConvertExpressionAst]) { $wr = $wr.Child }
                else { break }
            }
            $viaCmd = $false
            if ($wr -is [ParenExpressionAst] -or $wr -is [SubExpressionAst] -or $wr -is [ArrayExpressionAst]) {
                $viaCmd = ($wr.FindAll({ $args[0] -is [CommandAst] }, $true).Count -gt 0)
            } elseif ($wr -is [VariableExpressionAst]) {
                $rn = Get-VarBase $wr
                $viaCmd = ($rn -ieq '_' -or $rn -ieq 'PSItem' -or (Test-CmdVar $wr $rel))
            }
            if ($viaCmd) { Write-Violation $rel $a.Extent.StartLineNumber 'write through a command result not allowed' }
        }

        # $probes: only its three pinned sites, each at most once per file
        $probeVars = @($ast.FindAll({ $args[0] -is [VariableExpressionAst] }, $true) | Where-Object { (Get-VarBase $_) -ieq 'probes' })
        $siteTypes = @{}
        foreach ($pv in $probeVars) { $siteTypes[$pv.Extent.StartOffset] = Get-ProbesSiteType $pv $rel $ast }
        foreach ($pv in $probeVars) {
            $ty = $siteTypes[$pv.Extent.StartOffset]
            $dup = ($ty -ne 0) -and (@($siteTypes.Values | Where-Object { $_ -eq $ty }).Count -gt 1)
            if ($ty -eq 0 -or $dup) { Write-Violation $rel $pv.Extent.StartLineNumber 'use of $probes outside its pinned sites' }
        }

        # variables: $Host, $PSCmdlet, $ExecutionContext, splatting, drive-qualified names
        foreach ($v in $ast.FindAll({ $args[0] -is [VariableExpressionAst] }, $true)) {
            $ln = $v.Extent.StartLineNumber
            $vn = Get-VarBase $v
            if ($AgBadVariables -contains $vn) { Write-Violation $rel $ln ('variable not allowed: $' + $vn) }
            elseif ($vn -ieq 'ExecutionContext') {
                if (-not (Test-ExecChain $v $rel)) { Write-Violation $rel $ln '$ExecutionContext only allowed in its pinned chain in Write-ScanJson' }
            }
            if ($v.Splatted) { Write-Violation $rel $ln 'splatting not allowed' }
            if ($v.VariablePath.IsDriveQualified -and $v.VariablePath.DriveName -ine 'env') { Write-Violation $rel $ln 'drive-qualified variable not allowed' }
            elseif ($vn -match '^(\w+):' -and @('env', 'global', 'script', 'local', 'private', 'using') -notcontains $Matches[1]) {
                Write-Violation $rel $ln 'drive-qualified variable not allowed'    # e.g. ${variable:x}, which the parser treats as a plain name
            }
        }
        foreach ($w in @(Get-WrittenVars $ast)) {
            # neither collector.ps1 nor lib\Common.ps1 writes a scope-qualified variable, so none is allowed anywhere
            if (Test-ScopeQualified $w.Var) { Write-Violation $rel $w.Stmt.Extent.StartLineNumber 'write to a scope-qualified variable not allowed' }
            if ($w.Var.VariablePath.IsDriveQualified -and $w.Var.VariablePath.DriveName -ieq 'env') {
                Write-Violation $rel $w.Stmt.Extent.StartLineNumber 'assignment to an env: variable not allowed'
            }
        }

        # file redirection
        foreach ($r in $ast.FindAll({ $args[0] -is [FileRedirectionAst] }, $true)) {
            Write-Violation $rel $r.Extent.StartLineNumber 'file redirection not allowed'
        }

        # UNC and provider-drive strings
        foreach ($s in $ast.FindAll({ $args[0] -is [StringConstantExpressionAst] -or $args[0] -is [ExpandableStringExpressionAst] }, $true)) {
            if ($s.Value -match $AgBadPathPattern) { Write-Violation $rel $s.Extent.StartLineNumber 'UNC or provider-drive path string not allowed' }
        }

        # forbidden literals in the raw text (code, strings and comments)
        $raw = [IO.File]::ReadAllText($p.Full)
        foreach ($m in [regex]::Matches($raw, $AgForbiddenLiteral, 'IgnoreCase')) {
            Write-Violation $rel (Get-LineOf $raw $m.Index) ('forbidden literal: ' + ($m.Value -replace '\s+', ' '))
        }
    }

    return @($script:violations | Sort-Object -Unique)
}

if ($NoRun) { return }
try {
    $lines = @(Invoke-AgReadOnlyScan $Root)
} catch {
    Write-Output 'guard internal error'
    exit 1
}
if ($lines.Count -gt 0) {
    foreach ($l in $lines) { Write-Output $l }
    exit 1
}
Write-Output 'READ-ONLY OK'
exit 0
