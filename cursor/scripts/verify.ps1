[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$cursorRoot = Split-Path -Parent $PSScriptRoot
$pluginRoot = Join-Path $cursorRoot 'plugins/agent-advisor-cursor'
$agentsDir = Join-Path $pluginRoot 'agents'
$skillPath = Join-Path $pluginRoot 'skills/orchestration/SKILL.md'
$rulePath = Join-Path $pluginRoot 'rules/selective-routing.mdc'

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "FAIL: $Message" }
}

$required = @(
    (Join-Path $pluginRoot '.cursor-plugin/plugin.json'),
    (Join-Path $pluginRoot 'LICENSE'),
    $skillPath,
    (Join-Path $pluginRoot 'skills/orchestration/references/operations.md'),
    (Join-Path $pluginRoot 'skills/orchestration/references/role-contracts.md'),
    $rulePath,
    (Join-Path $cursorRoot 'README.md'),
    (Join-Path $cursorRoot 'docs/WORKFLOW.zh-TW.md')
)
foreach ($path in $required) {
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "required file missing: $path"
}

$manifest = Get-Content -LiteralPath (Join-Path $pluginRoot '.cursor-plugin/plugin.json') -Raw | ConvertFrom-Json
Assert-True ($manifest.name -eq 'agent-advisor-cursor') 'Cursor plugin name is wrong'
Assert-True ($manifest.version -eq '1.0.0') 'Cursor plugin version changed unexpectedly'
Write-Host 'PASS: Cursor plugin manifest'

$models = @{
    'advisor-composer-implementer.md' = 'composer-2.5'
    'advisor-sonnet-implementer.md' = 'claude-sonnet-5-thinking-high'
    'advisor-opus-reviewer.md' = 'claude-opus-5-thinking-high'
}
$expectedAgents = @($models.Keys | Sort-Object)
$actualAgents = @(Get-ChildItem -LiteralPath $agentsDir -File -Filter '*.md' | Sort-Object Name | Select-Object -ExpandProperty Name)
Assert-True (($actualAgents -join '|') -eq ($expectedAgents -join '|')) 'Cursor agent inventory differs from the exact three-role contract'
foreach ($entry in $models.GetEnumerator()) {
    $text = Get-Content -LiteralPath (Join-Path $agentsDir $entry.Key) -Raw
    Assert-True ($text -match "(?m)^model:\s+$([regex]::Escape($entry.Value))\s*$") "$($entry.Key) does not pin $($entry.Value)"
    Assert-True ($text -match '(?m)^name:\s+[a-z0-9-]+\s*$') "$($entry.Key) has an invalid name"
    Assert-True ($text -match '(?m)^description:\s+\S') "$($entry.Key) has no description"
}
$reviewer = Get-Content -LiteralPath (Join-Path $agentsDir 'advisor-opus-reviewer.md') -Raw
Assert-True ($reviewer -match '(?m)^readonly:\s+true\s*$') 'reviewer must be readonly: Cursor has no tool allowlist to fall back on'
Assert-True ($reviewer.Contains('Return exactly one verdict')) 'reviewer verdict contract is missing'
foreach ($name in @('advisor-composer-implementer.md', 'advisor-sonnet-implementer.md')) {
    $text = Get-Content -LiteralPath (Join-Path $agentsDir $name) -Raw
    Assert-True ($text -match '(?m)^readonly:\s+false\s*$') "$name must declare readonly: false explicitly"
}
Write-Host 'PASS: Cursor agent inventory, pinned models, and reviewer readonly flag'

$rule = Get-Content -LiteralPath $rulePath -Raw
Assert-True ($rule -match '(?m)^alwaysApply:\s+true\s*$') 'activation rule must always apply'
Assert-True ($rule -match '(?m)^description:\s+\S') 'activation rule has no description'
Assert-True ($rule.Contains('SELECTIVE ROUTE')) 'activation rule does not require the route declaration'
Write-Host 'PASS: Cursor always-apply activation rule'

$skill = Get-Content -LiteralPath $skillPath -Raw
foreach ($needle in @(
    'SELECTIVE ROUTE',
    'mode: solo | delegate | audit | full',
    'advisor-composer-implementer',
    'advisor-sonnet-implementer',
    'advisor-opus-reviewer',
    'rules/selective-routing.mdc'
)) {
    Assert-True ($skill.Contains($needle)) "Cursor orchestration skill omits: $needle"
}
$leaked = @(Get-ChildItem -LiteralPath $cursorRoot -Recurse -File | Where-Object { $_.Directory.Name -ne 'scripts' } | Where-Object {
    $text = Get-Content -LiteralPath $_.FullName -Raw
    $_.Extension -eq '.toml' -or $text.Contains('agent-advisor-claude') -or $text.Contains('permissionMode')
})
Assert-True ($leaked.Count -eq 0) 'Codex or Claude Code runtime contracts leaked into the Cursor edition'
Write-Host 'PASS: Cursor routing and platform-separation contracts'

Write-Host 'CURSOR VERIFY PASSED'
