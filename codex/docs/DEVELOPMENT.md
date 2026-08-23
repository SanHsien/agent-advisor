# Development

完整的 Windows-first fork、安裝、選路與維護流程請參閱
[WORKFLOW.zh-TW.md](WORKFLOW.zh-TW.md)；本頁只保留本機開發 gate 與暫存 fixture
規則。

Use PowerShell on Windows:

```powershell
pwsh -NoProfile -File tools/dev_check.ps1
```

The gate runs the PowerShell verifier and `git diff --check`. If `bash`, `jq`,
Python 3.11+ (`python3`, required for `tomllib`), and `rg` are available, it also
runs the authoritative POSIX verifier. Missing optional POSIX tools are reported
clearly and do not make the Windows gate fail. This version requirement adopts the
maintainer-documentation fix from upstream
[PR #24](https://github.com/DannyMac180/sol-advisor/pull/24).

To exercise an installer manually, always choose a disposable directory:

```powershell
$fixture = Join-Path ([IO.Path]::GetTempPath()) 'agent-advisor-codex-fixture'
& codex/plugins/agent-advisor-codex/scripts/install-agents.ps1 -TargetDir $fixture
& codex/plugins/agent-advisor-codex/scripts/install-agents.ps1 -TargetDir $fixture -Check -CheckRole luna -CheckRole sol
```

Remove the fixture manually after inspection. Never point development checks at your
real `$HOME/.codex/agents` directory.
