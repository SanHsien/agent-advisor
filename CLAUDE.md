# Repository guidance for Claude Code

Use Traditional Chinese for user-facing collaboration unless the user asks otherwise.

- Treat `codex/`, `claude/`, `cursor/`, and `antigravity/` as separate runtime
  implementations of the same four routes: `solo`, `delegate`, `audit`, and exceptional
  `full`.
- Do not translate one runtime's roles into another's syntax mechanically. Claude plugin
  agents are Markdown with Claude family aliases; Cursor agents pin model IDs and use
  `readonly`; Antigravity agents take a model tier and `commandExecutionPolicy`.
- Keep the root marketplace catalogs as thin discovery shims; runtime files belong in
  the matching platform subdirectory.
- `claude/templates/` holds material the user copies into their own `~/.claude/`.
  Nothing there runs from the repository, so keep the paths generic (`<you>`, not a
  real user name) and keep the wording in sync with
  `claude/docs/ACTIVATION.zh-TW.md`.
- Preserve Daniel McAteer's upstream attribution and the MIT license.
- Run `pwsh -NoProfile -File tools/dev_check.ps1` before reporting completion.
- PRs, pushes, releases, and repository settings must target
  `SanHsien/agent-advisor`; upstream contribution requires explicit consent in the
  current conversation.
