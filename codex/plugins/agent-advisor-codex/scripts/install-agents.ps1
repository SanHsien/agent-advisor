[CmdletBinding()]
param(
    [string]$TargetDir,
    [switch]$Check,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArguments = @()
)

$ErrorActionPreference = 'Stop'

function Stop-Install([string]$Message) { throw "ERROR: $Message" }
function Test-Exists([string]$Path) { return $null -ne (Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue) }
function Test-Reparse([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if ($null -eq $item) { return $false }
    # The ReparsePoint attribute alone is too broad on Windows. OneDrive Files
    # On-Demand sets it on every cloud placeholder, so a checkout inside a
    # OneDrive folder makes every shipped template look like a symlink attack
    # and blocks the install. Only real links carry a LinkType, so test that
    # instead -- symlinks and junctions are still rejected.
    return -not [string]::IsNullOrEmpty($item.LinkType)
}
function Get-State([string]$Destination, [string]$Template) {
    if (-not (Test-Exists $Destination)) { return 'missing' }
    $item = Get-Item -LiteralPath $Destination -Force -ErrorAction SilentlyContinue
    if ($null -eq $item -or $item.PSIsContainer -or (Test-Reparse $Destination)) { return 'unsafe' }
    try {
        $actual = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash
        $expected = (Get-FileHash -LiteralPath $Template -Algorithm SHA256).Hash
    } catch { return 'unreadable' }
    if ($actual -eq $expected) { return 'current' }
    return 'conflict'
}

$roleFiles = [ordered]@{
    luna = 'agent-advisor-codex-luna-implementer.toml'
    terra = 'agent-advisor-codex-terra-implementer.toml'
    sol = 'agent-advisor-codex-sol-reviewer.toml'
}
$selectedRoles = @()
for ($index = 0; $index -lt $RemainingArguments.Count; $index++) {
    if ($RemainingArguments[$index] -ne '-CheckRole') { Stop-Install "unknown argument: $($RemainingArguments[$index])" }
    if (++$index -ge $RemainingArguments.Count) { Stop-Install '-CheckRole requires luna, terra, or sol.' }
    foreach ($role in $RemainingArguments[$index] -split ',') {
        if (-not $roleFiles.Contains($role)) { Stop-Install "unknown -CheckRole '$role'; expected luna, terra, or sol." }
        $selectedRoles += $role
    }
}
if ($selectedRoles.Count) { $Check = $true }

$scriptDir = Split-Path -Parent $PSCommandPath
$templateDir = Join-Path (Split-Path -Parent $scriptDir) 'agents'
if ($PSBoundParameters.ContainsKey('TargetDir')) {
    if ([string]::IsNullOrWhiteSpace($TargetDir)) { Stop-Install '-TargetDir was explicitly supplied but is null, empty, or whitespace.' }
} else {
    $base = if ($env:CODEX_HOME) { $env:CODEX_HOME } elseif ($env:USERPROFILE) { Join-Path $env:USERPROFILE '.codex' } else { Stop-Install 'CODEX_HOME and USERPROFILE are unset; pass -TargetDir explicitly.' }
    $TargetDir = Join-Path $base 'agents'
}
$TargetDir = [IO.Path]::GetFullPath($TargetDir)
if ($TargetDir -eq [IO.Path]::GetPathRoot($TargetDir)) { Stop-Install 'refusing to use a filesystem root as an agent target directory.' }
if ((Test-Exists $TargetDir) -and ((Test-Reparse $TargetDir) -or -not (Test-Path -LiteralPath $TargetDir -PathType Container))) { Stop-Install "target directory is not a real directory: $TargetDir" }

$roles = [ordered]@{}
foreach ($role in $roleFiles.Keys) {
    $template = Join-Path $templateDir $roleFiles[$role]
    $item = Get-Item -LiteralPath $template -Force -ErrorAction SilentlyContinue
    if ($null -eq $item -or $item.PSIsContainer -or (Test-Reparse $template)) { Stop-Install "shipped template is missing or unsafe: $template" }
    $destination = Join-Path $TargetDir $roleFiles[$role]
    $roles[$role] = @{ Template = $template; Destination = $destination; State = (Get-State $destination $template) }
}

if ($Check) {
    $checkRoles = if ($selectedRoles.Count) { @($selectedRoles | Select-Object -Unique) } else { @($roleFiles.Keys) }
    foreach ($role in $checkRoles) {
        if ($roles[$role].State -ne 'current') { Stop-Install "$role template is $($roles[$role].State), not the current exact file: $($roles[$role].Destination)" }
    }
    Write-Host 'CHECK PASSED: selected Agent Advisor for Codex role templates exactly match shipped templates.'
    exit 0
}

foreach ($role in $roleFiles.Keys) {
    if ($roles[$role].State -notin @('missing', 'current')) { Stop-Install "$role destination is $($roles[$role].State) and will not be replaced: $($roles[$role].Destination)" }
}
if (-not (Test-Exists $TargetDir)) { [IO.Directory]::CreateDirectory($TargetDir) | Out-Null }
if ((Test-Reparse $TargetDir) -or -not (Test-Path -LiteralPath $TargetDir -PathType Container)) { Stop-Install "target directory changed after preflight: $TargetDir" }

foreach ($role in $roleFiles.Keys) {
    $entry = $roles[$role]
    if ((Get-State $entry.Destination $entry.Template) -ne $entry.State) { Stop-Install "$role destination changed after preflight." }
    if ($entry.State -eq 'current') { Write-Host "ALREADY CURRENT: $($entry.Destination)"; continue }
    $stage = Join-Path $TargetDir ('.agent-advisor-codex-agent.' + [guid]::NewGuid().ToString('N'))
    Copy-Item -LiteralPath $entry.Template -Destination $stage
    try {
        if (Test-Exists $entry.Destination) { Stop-Install "destination appeared after preflight: $($entry.Destination)" }
        [IO.File]::Move($stage, $entry.Destination)
        Write-Host "INSTALLED: $($entry.Destination)"
    } finally {
        if (Test-Exists $stage) { Remove-Item -LiteralPath $stage -Force }
    }
}
foreach ($role in $roleFiles.Keys) {
    if ((Get-State $roles[$role].Destination $roles[$role].Template) -ne 'current') { Stop-Install "post-install exactness check failed: $($roles[$role].Destination)" }
}
Write-Host 'INSTALL PASSED: Luna, Terra, and Sol role profiles exactly match Agent Advisor for Codex.'
