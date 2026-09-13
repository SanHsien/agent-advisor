[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$agRoot = Split-Path -Parent $PSScriptRoot
$pluginRoot = Join-Path $agRoot 'plugins/agent-advisor-antigravity'
$agentsDir = Join-Path $pluginRoot 'agents'
$skillPath = Join-Path $pluginRoot 'skills/orchestration/SKILL.md'
$rulePath = Join-Path $pluginRoot 'rules/selective-routing.md'

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "FAIL: $Message" }
}

$required = @(
    (Join-Path $pluginRoot 'plugin.json'),
    (Join-Path $pluginRoot 'LICENSE'),
    $skillPath,
    (Join-Path $pluginRoot 'skills/orchestration/references/operations.md'),
    (Join-Path $pluginRoot 'skills/orchestration/references/role-contracts.md'),
    $rulePath,
    (Join-Path $agRoot 'README.md'),
    (Join-Path $agRoot 'docs/WORKFLOW.zh-TW.md'),
    (Join-Path $agRoot 'templates/README.md'),
    (Join-Path $agRoot 'templates/AGENTS.md.snippet.md'),
    (Join-Path $agRoot 'templates/hooks-example.json'),
    (Join-Path $agRoot 'scripts/fix_hook_quoting.py')
)
foreach ($path in $required) {
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "required file missing: $path"
}

$manifest = Get-Content -LiteralPath (Join-Path $pluginRoot 'plugin.json') -Raw | ConvertFrom-Json
Assert-True ($manifest.name -eq 'agent-advisor-antigravity') 'Antigravity plugin name is wrong'
Assert-True (-not (Test-Path -LiteralPath (Join-Path $pluginRoot '.claude-plugin'))) 'Antigravity reads plugin.json at the plugin root, not .claude-plugin/'
Assert-True (-not (Test-Path -LiteralPath (Join-Path $pluginRoot '.cursor-plugin'))) 'Antigravity reads plugin.json at the plugin root, not .cursor-plugin/'
Write-Host 'PASS: Antigravity plugin manifest and root placement'

$tiers = @{
    'advisor-flash-implementer.md' = 'flash'
    'advisor-pro-implementer.md' = 'pro'
    'advisor-pro-reviewer.md' = 'pro'
}
$expectedAgents = @($tiers.Keys | Sort-Object)
$actualAgents = @(Get-ChildItem -LiteralPath $agentsDir -File -Filter '*.md' | Sort-Object Name | Select-Object -ExpandProperty Name)
Assert-True (($actualAgents -join '|') -eq ($expectedAgents -join '|')) 'Antigravity agent inventory differs from the exact three-role contract'
foreach ($entry in $tiers.GetEnumerator()) {
    $text = Get-Content -LiteralPath (Join-Path $agentsDir $entry.Key) -Raw
    Assert-True ($text -match "(?m)^model:\s+$($entry.Value)\s*$") "$($entry.Key) must pin the $($entry.Value) tier, not a dated model ID"
    Assert-True ($text -match '(?m)^name:\s+[a-z0-9-]+\s*$') "$($entry.Key) has an invalid name"
    Assert-True ($text -match '(?m)^subagent:\s+true\s*$') "$($entry.Key) is not invokable as a subagent"
    Assert-True ($text -match '(?m)^mainAgent:\s+false\s*$') "$($entry.Key) must not be selectable as the primary agent"
}
$reviewer = Get-Content -LiteralPath (Join-Path $agentsDir 'advisor-pro-reviewer.md') -Raw
Assert-True ($reviewer -match '(?m)^commandExecutionPolicy:\s+off\s*$') 'reviewer must deny shell execution'
Assert-True ($reviewer.Contains('Return exactly one verdict')) 'reviewer verdict contract is missing'
Assert-True (-not ($reviewer -match '(?m)^tools:')) 'the tools vocabulary is undocumented; a guessed identifier must never be shipped'
Write-Host 'PASS: Antigravity agent inventory, model tiers, and reviewer execution policy'

$rule = Get-Content -LiteralPath $rulePath -Raw
Assert-True (-not $rule.TrimStart().StartsWith('---')) 'GEMINI.md/AGENTS.md-style rules take no frontmatter'
Assert-True ($rule.Contains('SELECTIVE ROUTE')) 'activation rule does not require the route declaration'
Write-Host 'PASS: Antigravity always-active rule'

$skill = Get-Content -LiteralPath $skillPath -Raw
foreach ($needle in @(
    'SELECTIVE ROUTE',
    'mode: solo | delegate | audit | full',
    'advisor-flash-implementer',
    'advisor-pro-implementer',
    'advisor-pro-reviewer',
    'rules/selective-routing.md'
)) {
    Assert-True ($skill.Contains($needle)) "Antigravity orchestration skill omits: $needle"
}
$leaked = @(Get-ChildItem -LiteralPath $agRoot -Recurse -File | Where-Object { $_.Directory.Name -ne 'scripts' } | Where-Object {
    $text = Get-Content -LiteralPath $_.FullName -Raw
    $_.Extension -eq '.toml' -or $text.Contains('agent-advisor-claude') -or $text.Contains('agent-advisor-cursor') -or $text.Contains('alwaysApply')
})
Assert-True ($leaked.Count -eq 0) 'Codex, Claude Code, or Cursor runtime contracts leaked into the Antigravity edition'
Write-Host 'PASS: Antigravity routing and platform-separation contracts'

# Antigravity splits a hook command into argv itself: a quoted script path keeps its
# quotes inside the filename and fails with [Errno 22]. The example must never regress
# to the shell-style quoted form that is correct for Claude Code.
$hooksExampleRaw = Get-Content -LiteralPath (Join-Path $agRoot 'templates/hooks-example.json') -Raw
$hooksExample = $hooksExampleRaw | ConvertFrom-Json
$commands = @()
function Get-HookCommand($node) {
    if ($null -eq $node) { return }
    if ($node -is [System.Management.Automation.PSCustomObject]) {
        foreach ($prop in $node.PSObject.Properties) {
            if ($prop.Name -eq 'command' -and $prop.Value -is [string]) {
                $script:commands += $prop.Value
            } else {
                Get-HookCommand $prop.Value
            }
        }
    } elseif ($node -is [System.Collections.IEnumerable] -and $node -isnot [string]) {
        foreach ($item in $node) { Get-HookCommand $item }
    }
}
Get-HookCommand $hooksExample
Assert-True ($commands.Count -gt 0) 'hooks example declares no hook command'
foreach ($command in $commands) {
    Assert-True (-not $command.Contains('"')) "hook path must not be quoted: $command"
    Assert-True ($command.StartsWith('python ')) "hook must invoke python, not a bare bash: $command"
    Assert-True (-not $command.Substring(7).Contains(' ')) "no shell means no spaces in the path: $command"
    Assert-True ($command.Contains('<you>')) "template must use the generic placeholder: $command"
}

$fixer = Get-Content -LiteralPath (Join-Path $agRoot 'scripts/fix_hook_quoting.py') -Raw
Assert-True ($fixer.Contains('--apply')) 'the repair script must default to a dry run'
Assert-True ($fixer.Contains('shutil.copy2')) 'the repair script must back up before writing'
Write-Host 'PASS: Antigravity hook command shape and repair script'

Write-Host 'ANTIGRAVITY VERIFY PASSED'
