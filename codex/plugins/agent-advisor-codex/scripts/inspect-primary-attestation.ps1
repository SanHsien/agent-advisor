[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$prefix = 'AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION: '

function Stop-Inspection([string]$Message) {
    throw "PRIMARY_ATTESTATION REFUSED: $Message"
}

if (-not [string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
    $CodexHome = $env:CODEX_HOME
} else {
    $CodexHome = Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex'
}

$resolvedHome = [IO.Path]::GetFullPath($CodexHome)
$agentsPath = Join-Path $resolvedHome 'AGENTS.md'
$overridePath = Join-Path $resolvedHome 'AGENTS.override.md'

if (Test-Path -LiteralPath $overridePath) {
    Stop-Inspection "user-level override exists: $overridePath"
}
if (-not (Test-Path -LiteralPath $agentsPath -PathType Leaf)) {
    Stop-Inspection "regular user-level AGENTS.md is missing: $agentsPath"
}

$item = Get-Item -LiteralPath $agentsPath -Force
# LinkType, not the ReparsePoint attribute: OneDrive Files On-Demand sets that
# attribute on every cloud placeholder, so a file living under OneDrive would be
# rejected as a link. Only real symlinks and junctions have a LinkType.
if (-not [string]::IsNullOrEmpty($item.LinkType)) {
    Stop-Inspection "user-level AGENTS.md is a reparse point: $agentsPath"
}
if ($item.Length -gt 32768) {
    Stop-Inspection "user-level AGENTS.md exceeds 32768 bytes: $agentsPath"
}

$lines = Get-Content -LiteralPath $agentsPath
$markers = @($lines | Where-Object { $_ -cmatch '^AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION:' })
$count = $markers.Count
if ($count -ne 1) {
    Stop-Inspection "expected exactly one attestation marker, found $count"
}
$pair = $markers[0].Substring($prefix.Length)
if ($markers[0] -cne ($prefix + $pair) -or $pair -cnotin @('gpt-6-astra/low', 'gpt-5.6-sol/high')) {
    Stop-Inspection 'unsupported primary model/effort pair'
}
$model, $effort = $pair.Split('/')

Write-Output 'PRIMARY_ATTESTATION PASSED'
Write-Output "source=$agentsPath"
Write-Output 'provenance=user-level-file'
Write-Output "model=$model"
Write-Output "effort=$effort"
