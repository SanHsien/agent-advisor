[CmdletBinding()]
param(
    [string]$BaseRef
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

function Invoke-Gate {
    param([string]$Name, [scriptblock]$Command)
    Write-Host "==> $Name"
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE." }
}

Invoke-Gate 'Codex PowerShell verifier' { & pwsh -NoProfile -File (Join-Path $repoRoot 'codex/plugins/agent-advisor-codex/scripts/verify.ps1') }
Invoke-Gate 'Claude PowerShell verifier' { & pwsh -NoProfile -File (Join-Path $repoRoot 'claude/scripts/verify.ps1') }
Invoke-Gate 'Cursor PowerShell verifier' { & pwsh -NoProfile -File (Join-Path $repoRoot 'cursor/scripts/verify.ps1') }
Invoke-Gate 'Antigravity PowerShell verifier' { & pwsh -NoProfile -File (Join-Path $repoRoot 'antigravity/scripts/verify.ps1') }
$python = @('python', 'python3') | Where-Object { Get-Command $_ -ErrorAction SilentlyContinue } | Select-Object -First 1
if ($python) {
    # No -t: with an absolute start directory unittest treats it as the top level, so
    # tests/ needs no __init__.py. Passing -t $repoRoot would demand a package there.
    Invoke-Gate 'Repository unit tests' { & $python -m unittest discover -s (Join-Path $repoRoot 'tests') -p 'test_*.py' }
    # Relative links between the four editions' docs break silently: nothing errors,
    # the link just stops resolving and the next reader gets a 404 instead of the
    # contract they were sent to read.
    Invoke-Gate 'Markdown relative links' { & $python (Join-Path $repoRoot 'tools/check_links.py') }
} else {
    Write-Host 'SKIP: unit tests and the link check require python on PATH. CI runs them on every push and remains authoritative for them.'
}

Invoke-Gate 'git diff --check (unstaged)' { git -C $repoRoot diff --check }
Invoke-Gate 'git diff --cached --check (staged)' { git -C $repoRoot diff --cached --check }

if (-not [string]::IsNullOrWhiteSpace($BaseRef)) {
    $baseCommit = $null
    if ($BaseRef -notmatch '^[0]+$') {
        $baseCommit = (& git -C $repoRoot rev-parse --verify "$BaseRef^{commit}" 2>$null | Select-Object -First 1)
        if ($LASTEXITCODE -ne 0) { $baseCommit = $null }
    }
    if ($baseCommit) {
        Invoke-Gate "git diff --check $baseCommit..HEAD" { git -C $repoRoot diff --check "$baseCommit..HEAD" }
    } else {
        Write-Host "WARN: BaseRef '$BaseRef' is unavailable or all-zero; checking HEAD commit instead."
        Invoke-Gate 'git show --check HEAD fallback' { git -C $repoRoot show --check --format= HEAD }
    }
}

$optional = @('bash', 'jq', 'python3', 'rg')
$missing = @($optional | Where-Object { -not (Get-Command $_ -ErrorAction SilentlyContinue) })
if ($missing.Count -eq 0) {
    Invoke-Gate 'Codex POSIX verifier' { bash (Join-Path $repoRoot 'codex/plugins/agent-advisor-codex/scripts/verify.sh') }
    Invoke-Gate 'Claude POSIX verifier' { bash (Join-Path $repoRoot 'claude/scripts/verify.sh') }
    Invoke-Gate 'Cursor POSIX verifier' { bash (Join-Path $repoRoot 'cursor/scripts/verify.sh') }
    Invoke-Gate 'Antigravity POSIX verifier' { bash (Join-Path $repoRoot 'antigravity/scripts/verify.sh') }
} else {
    Write-Host "SKIP: POSIX verifier requires optional tools not found: $($missing -join ', '). Windows gate remains authoritative."
}

Write-Host 'DEV CHECK PASSED'
