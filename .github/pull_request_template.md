## Summary

<!-- State the observable change and whether it is fork-only or an upstream alignment. -->

## Validation

- [ ] `pwsh -NoProfile -File tools/dev_check.ps1`
- [ ] `sh codex/plugins/agent-advisor-codex/scripts/verify.sh` (POSIX/WSL)
- [ ] `sh claude/scripts/verify.sh` (POSIX/WSL)
- [ ] `git diff --check`

## Scope and attribution

- [ ] I retained upstream attribution and the MIT license.
- [ ] I did not test against a real user Codex agent directory.
- [ ] I kept Codex and Claude runtime files in their platform subdirectories.
- [ ] This targets `SanHsien/agent-advisor`.
