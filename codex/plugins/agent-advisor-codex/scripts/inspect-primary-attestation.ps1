[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$marker = 'AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION: gpt-5.6-sol/high'

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
if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    Stop-Inspection "user-level AGENTS.md is a reparse point: $agentsPath"
}
if ($item.Length -gt 32768) {
    Stop-Inspection "user-level AGENTS.md exceeds 32768 bytes: $agentsPath"
}

$lines = Get-Content -LiteralPath $agentsPath
$count = @($lines | Where-Object { $_ -ceq $marker }).Count
if ($count -ne 1) {
    Stop-Inspection "expected exactly one attestation marker, found $count"
}

Write-Output 'PRIMARY_ATTESTATION PASSED'
Write-Output "source=$agentsPath"
Write-Output 'provenance=user-level-file'
Write-Output 'model=gpt-5.6-sol'
Write-Output 'effort=high'
