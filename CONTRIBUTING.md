# Contributing

Thank you for improving Agent Advisor. Keep changes scoped, retain Daniel McAteer's
upstream attribution and MIT license, and identify whether a change affects
the Codex edition, Claude Code edition, or shared repository layer.

Before opening a pull request, run:

```powershell
pwsh -NoProfile -File tools/dev_check.ps1
git diff --check
```

On POSIX or WSL, also run both platform verifiers:

```sh
sh codex/plugins/agent-advisor-codex/scripts/verify.sh
sh claude/scripts/verify.sh
```

Report the commands and their actual results. Do not test the Codex installer against
a real agent directory; use the provided fixture-based verifier. Validate Claude
plugin changes with `claude plugin validate claude` when the installed CLI supports it.
