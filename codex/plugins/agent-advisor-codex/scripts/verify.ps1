[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $PSCommandPath
$pluginDir = Split-Path -Parent $scriptDir
$codexRoot = Split-Path -Parent (Split-Path -Parent $pluginDir)
$repoRoot = Split-Path -Parent $codexRoot
$installer = Join-Path $scriptDir 'install-agents.ps1'
$inspector = Join-Path $scriptDir 'inspect-primary-attestation.ps1'
$agentsDir = Join-Path $pluginDir 'agents'
$modelHook = Join-Path $pluginDir 'hooks/observe_primary_model.py'
$hooksConfig = Join-Path $pluginDir 'hooks/hooks.json'

function Assert-True([bool]$Condition, [string]$Message) { if (-not $Condition) { throw "FAIL: $Message" } }
function Invoke-ExpectedFailure([scriptblock]$Command, [string]$Message) {
    try { & $Command; throw "FAIL: $Message" }
    catch { if ($_.Exception.Message -eq "FAIL: $Message") { throw }; Write-Host "PASS: $Message" }
}

$rootMarket = Get-Content -LiteralPath (Join-Path $repoRoot '.agents/plugins/marketplace.json') -Raw | ConvertFrom-Json
$localMarket = Get-Content -LiteralPath (Join-Path $codexRoot '.agents/plugins/marketplace.json') -Raw | ConvertFrom-Json
$manifest = Get-Content -LiteralPath (Join-Path $pluginDir '.codex-plugin/plugin.json') -Raw | ConvertFrom-Json
Assert-True (Test-Path -LiteralPath (Join-Path $pluginDir 'LICENSE') -PathType Leaf) 'plugin-local MIT license is missing'
Assert-True (Test-Path -LiteralPath $modelHook -PathType Leaf) 'advisory model hook is missing'
Assert-True (Test-Path -LiteralPath $hooksConfig -PathType Leaf) 'hook registration is missing'
Assert-True ($rootMarket.name -eq 'agent-advisor') 'root Codex marketplace name is wrong'
Assert-True ($rootMarket.plugins[0].name -eq 'agent-advisor-codex') 'root Codex plugin ID is wrong'
Assert-True ($rootMarket.plugins[0].source.path -eq './codex/plugins/agent-advisor-codex') 'root Codex source is wrong'
Assert-True ($localMarket.plugins[0].source.path -eq './plugins/agent-advisor-codex') 'Codex-local source is wrong'
Assert-True ($manifest.name -eq 'agent-advisor-codex') 'manifest plugin ID is wrong'
Assert-True ($manifest.version -eq '1.0.0') 'manifest version changed unexpectedly'
Assert-True ($manifest.interface.displayName -eq 'Agent Advisor for Codex') 'manifest product name is wrong'
Assert-True ($manifest.author.name -eq 'Daniel McAteer') 'original author attribution is missing'
Write-Host 'PASS: Codex marketplace, manifest, product name, and attribution'

$expected = [ordered]@{
    'agent-advisor-codex-luna-implementer.toml' = @('agent_advisor_codex_luna_implementer', 'gpt-5.6-luna', 'max')
    'agent-advisor-codex-terra-implementer.toml' = @('agent_advisor_codex_terra_implementer', 'gpt-5.6-terra', 'high')
    'agent-advisor-codex-sol-reviewer.toml' = @('agent_advisor_codex_sol_reviewer', 'gpt-5.6-sol', 'high')
}
$actual = @(Get-ChildItem -LiteralPath $agentsDir -File -Filter '*.toml' | Sort-Object Name | Select-Object -ExpandProperty Name)
Assert-True (($actual -join '|') -eq (($expected.Keys | Sort-Object) -join '|')) 'Codex role inventory differs from the exact three-role contract'
foreach ($file in $expected.Keys) {
    $text = Get-Content -LiteralPath (Join-Path $agentsDir $file) -Raw
    Assert-True ($text.Contains("name = `"$($expected[$file][0])`"")) "$file has the wrong role name"
    Assert-True ($text.Contains("model = `"$($expected[$file][1])`"")) "$file has the wrong model"
    Assert-True ($text.Contains("model_reasoning_effort = `"$($expected[$file][2])`"")) "$file has the wrong effort"
}
Assert-True ((Get-Content -LiteralPath (Join-Path $agentsDir 'agent-advisor-codex-sol-reviewer.toml') -Raw).Contains('sandbox_mode = "read-only"')) 'Sol reviewer no longer requests read-only sandbox'
Write-Host 'PASS: Codex exact role IDs, models, efforts, and reviewer sandbox request'

$skill = Get-Content -LiteralPath (Join-Path $pluginDir 'skills/orchestration/SKILL.md') -Raw
$operations = Get-Content -LiteralPath (Join-Path $pluginDir 'skills/orchestration/references/operations.md') -Raw
foreach ($needle in @('SELECTIVE ROUTE', 'mode: solo | delegate | audit | full', 'AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION: gpt-5.6-sol/high')) {
    Assert-True ($skill.Contains($needle)) "Codex orchestration skill omits: $needle"
}
foreach ($roleId in @('agent_advisor_codex_luna_implementer', 'agent_advisor_codex_terra_implementer', 'agent_advisor_codex_sol_reviewer')) {
    Assert-True ($operations.Contains($roleId)) "Codex operations reference omits: $roleId"
}
Write-Host 'PASS: Codex routing and primary-attestation contracts'

$fixtureRoot = Join-Path ([IO.Path]::GetTempPath()) ('agent-advisor-codex-verify-' + [guid]::NewGuid().ToString('N'))
$hadCodexHome = Test-Path Env:CODEX_HOME
$previousCodexHome = $env:CODEX_HOME
try {
    $fakeHome = Join-Path $fixtureRoot 'home'
    [IO.Directory]::CreateDirectory($fakeHome) | Out-Null
    $env:CODEX_HOME = $fakeHome
    Set-Content -LiteralPath (Join-Path $fakeHome 'AGENTS.md') -Value 'AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION: gpt-5.6-sol/high'
    $output = & $inspector
    Assert-True ($output -contains 'PRIMARY_ATTESTATION PASSED') 'valid primary attestation was refused'
    Assert-True ($output -contains 'provenance=user-level-file') 'inspector omitted verified provenance'

    Invoke-ExpectedFailure { & $installer -TargetDir '' } 'explicit empty target is refused'
    Invoke-ExpectedFailure { & $installer -TargetDir $null } 'explicit null target is refused'
    $clean = Join-Path $fixtureRoot 'clean'
    & $installer -TargetDir $clean
    & $installer -TargetDir $clean -Check
    & $installer -TargetDir $clean -CheckRole luna -CheckRole sol
    Add-Content -LiteralPath (Join-Path $clean 'agent-advisor-codex-terra-implementer.toml') -Value 'modified'
    Invoke-ExpectedFailure { & $installer -TargetDir $clean -Check -CheckRole terra } 'modified selected role is refused'
    & $installer -TargetDir $clean -Check -CheckRole luna -CheckRole sol
    Invoke-ExpectedFailure { & $installer -TargetDir $clean } 'conflicting install is refused'
    Write-Host 'PASS: Codex inspector and fail-closed installer fixtures'
} finally {
    if ($hadCodexHome) { $env:CODEX_HOME = $previousCodexHome } else { Remove-Item Env:CODEX_HOME -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $fixtureRoot) { Remove-Item -LiteralPath $fixtureRoot -Recurse -Force }
}

Write-Host 'CODEX VERIFY PASSED'
