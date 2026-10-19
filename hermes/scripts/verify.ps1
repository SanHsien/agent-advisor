[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$hermesRoot = Split-Path -Parent $PSScriptRoot
$skillRoot = Join-Path $hermesRoot 'skills/agent-advisor-orchestration'
$skill = Get-Content -LiteralPath (Join-Path $skillRoot 'SKILL.md') -Raw
foreach ($needle in @('name: agent-advisor-orchestration', 'SELECTIVE ROUTE', 'delegate_task', 'solo', 'delegate', 'audit', 'full', 'cost-policy.md', 'behaviorally read-only')) {
    if (-not $skill.Contains($needle)) { throw "Hermes contract missing: $needle" }
}
$cost = Get-Content -LiteralPath (Join-Path $skillRoot 'references/cost-policy.md') -Raw
foreach ($needle in @('unknown', 'task_id', 'HEAD', 'provider', '429')) {
    if (-not $cost.Contains($needle)) { throw "Hermes cost contract missing: $needle" }
}
if ($skill -match 'C:[/\\]Users[/\\]') { throw 'Hermes skill contains a machine-specific path' }
Write-Host 'HERMES CONTRACT VERIFY PASSED (package evidence only)'
