[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$claudeRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $claudeRoot
$pluginRoot = Join-Path $claudeRoot 'plugins/agent-advisor-claude'
$agentsDir = Join-Path $pluginRoot 'agents'
$skillPath = Join-Path $pluginRoot 'skills/orchestration/SKILL.md'

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "FAIL: $Message" }
}

$required = @(
    (Join-Path $repoRoot '.claude-plugin/marketplace.json'),
    (Join-Path $claudeRoot '.claude-plugin/marketplace.json'),
    (Join-Path $pluginRoot '.claude-plugin/plugin.json'),
    (Join-Path $pluginRoot 'LICENSE'),
    $skillPath,
    (Join-Path $pluginRoot 'skills/orchestration/references/operations.md'),
    (Join-Path $pluginRoot 'skills/orchestration/references/role-contracts.md'),
    (Join-Path $claudeRoot 'README.md'),
    (Join-Path $claudeRoot 'docs/WORKFLOW.zh-TW.md')
)
foreach ($path in $required) {
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "required file missing: $path"
}

$rootMarketplace = Get-Content -LiteralPath (Join-Path $repoRoot '.claude-plugin/marketplace.json') -Raw | ConvertFrom-Json
$localMarketplace = Get-Content -LiteralPath (Join-Path $claudeRoot '.claude-plugin/marketplace.json') -Raw | ConvertFrom-Json
$manifest = Get-Content -LiteralPath (Join-Path $pluginRoot '.claude-plugin/plugin.json') -Raw | ConvertFrom-Json
Assert-True ($rootMarketplace.name -eq 'agent-advisor') 'root Claude marketplace name is wrong'
Assert-True ($rootMarketplace.plugins.Count -eq 1) 'root Claude marketplace must expose one plugin'
Assert-True ($rootMarketplace.plugins[0].source -eq './claude/plugins/agent-advisor-claude') 'root Claude marketplace source is wrong'
Assert-True ($localMarketplace.plugins[0].source -eq './plugins/agent-advisor-claude') 'Claude-local marketplace source is wrong'
Assert-True ($manifest.name -eq 'agent-advisor-claude') 'Claude plugin name is wrong'
Assert-True ($manifest.version -eq '1.0.0') 'Claude plugin version changed unexpectedly'
Assert-True ($manifest.repository -eq 'https://github.com/SanHsien/agent-advisor') 'Claude plugin repository is wrong'
Write-Host 'PASS: Claude marketplace and plugin JSON'

$expectedAgents = @(
    'advisor-haiku-implementer.md',
    'advisor-opus-reviewer.md',
    'advisor-sonnet-implementer.md'
)
$actualAgents = @(Get-ChildItem -LiteralPath $agentsDir -File -Filter '*.md' | Sort-Object Name | Select-Object -ExpandProperty Name)
Assert-True (($actualAgents -join '|') -eq ($expectedAgents -join '|')) 'Claude agent inventory differs from the exact three-role contract'

$models = @{
    'advisor-haiku-implementer.md' = 'haiku'
    'advisor-sonnet-implementer.md' = 'sonnet'
    'advisor-opus-reviewer.md' = 'opus'
}
foreach ($entry in $models.GetEnumerator()) {
    $text = Get-Content -LiteralPath (Join-Path $agentsDir $entry.Key) -Raw
    Assert-True ($text -match "(?m)^model:\s+$($entry.Value)\s*$") "$($entry.Key) does not pin $($entry.Value)"
    Assert-True ($text -match '(?m)^name:\s+[a-z0-9-]+\s*$') "$($entry.Key) has an invalid name"
}
$reviewer = Get-Content -LiteralPath (Join-Path $agentsDir 'advisor-opus-reviewer.md') -Raw
Assert-True ($reviewer -match '(?m)^tools:\s+Read, Glob, Grep, Bash\s*$') 'reviewer tool allowlist drifted'
Assert-True ($reviewer -match '(?m)^disallowedTools:.*Edit.*Write') 'reviewer does not explicitly deny file-edit tools'
Assert-True ($reviewer.Contains('Return exactly one verdict')) 'reviewer verdict contract is missing'
Write-Host 'PASS: Claude native agent inventory, model aliases, and reviewer restrictions'

$skill = Get-Content -LiteralPath $skillPath -Raw
foreach ($needle in @(
    'SELECTIVE ROUTE',
    'mode: solo | delegate | audit | full',
    'agent-advisor-claude:advisor-haiku-implementer',
    'agent-advisor-claude:advisor-sonnet-implementer',
    'agent-advisor-claude:advisor-opus-reviewer',
    'substitution warning',
    'git status --short'
)) {
    Assert-True ($skill.Contains($needle)) "Claude orchestration skill omits: $needle"
}
$forbiddenFiles = @(Get-ChildItem -LiteralPath $claudeRoot -Recurse -File | Where-Object { $_.Extension -eq '.toml' -or $_.Name -like 'inspect-primary-attestation*' })
Assert-True ($forbiddenFiles.Count -eq 0) 'Codex-only TOML or attestation inspector leaked into the Claude edition'
Write-Host 'PASS: Claude routing and platform-separation contracts'

$templatesDir = Join-Path $claudeRoot 'templates'
$snippetPath = Join-Path $templatesDir 'claude-md-snippet.md'
$examplePath = Join-Path $templatesDir 'settings-example.json'
$hookPath = Join-Path $templatesDir 'session-start-activation.py'
$activationAssets = @(
    (Join-Path $claudeRoot 'docs/ACTIVATION.zh-TW.md'),
    (Join-Path $templatesDir 'README.md'),
    $snippetPath,
    $examplePath,
    $hookPath
)
foreach ($path in $activationAssets) {
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "activation asset missing: $path"
}

$settingsExample = Get-Content -LiteralPath $examplePath -Raw | ConvertFrom-Json
Assert-True ($settingsExample.model -like 'claude-opus-*') 'settings example must default to the Opus family'
Assert-True (@('low', 'medium', 'high', 'xhigh', 'max') -contains $settingsExample.effortLevel) 'settings example uses an unsupported effortLevel'
$hookCommand = $settingsExample.hooks.SessionStart[0].hooks[0].command
Assert-True ($hookCommand.StartsWith('python ')) 'hook command must invoke python, not a bare bash that resolves to WSL on Windows'
Assert-True ($hookCommand.Contains('session-start-activation.py')) 'hook command does not point at the shipped hook'

$snippetText = Get-Content -LiteralPath $snippetPath -Raw
foreach ($needle in @(
    'agent-advisor-claude:orchestration',
    'SELECTIVE ROUTE',
    'solo',
    'delegate',
    'audit',
    'full'
)) {
    Assert-True ($snippetText.Contains($needle)) "CLAUDE.md snippet omits: $needle"
}
Assert-True ($snippetText.Contains('不報錯')) 'CLAUDE.md snippet lost its skip-without-error fallback'
Assert-True ($snippetText.Contains('without raising an error')) 'English snippet lost its skip-without-error fallback'

$hookText = Get-Content -LiteralPath $hookPath -Raw
Assert-True ($hookText.Contains('additionalContext')) 'hook template no longer injects additionalContext'

$leakedPaths = @(Get-ChildItem -LiteralPath $templatesDir -Recurse -File | Where-Object {
    $text = Get-Content -LiteralPath $_.FullName -Raw
    $text.Contains('Users\SanHsien') -or $text.Contains('Users/SanHsien')
})
Assert-True ($leakedPaths.Count -eq 0) 'templates must use a generic <you> placeholder, not a real home directory'
Write-Host 'PASS: Claude activation guide and copy-paste templates'

Write-Host 'CLAUDE VERIFY PASSED'
