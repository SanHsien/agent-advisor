# Agent Advisor for Claude Code

Agent Advisor for Claude Code is the Claude Code edition of
[Agent Advisor](https://github.com/SanHsien/agent-advisor). It adapts the selective
routing design of Daniel McAteer's upstream project to Claude Code's native plugin skills
and Markdown subagents; it does not run Codex or translate Codex configuration at
runtime.

The primary Opus session owns architecture, route selection, verification, and final
acceptance. It stays `solo` by default and uses one auxiliary only when the task risk
justifies it:

| Route | Native Claude Code delivery |
| --- | --- |
| `solo` | Opus plans, implements, tests, and self-reviews. |
| `delegate` | Haiku handles bounded work or Sonnet handles judgment-heavy/high-risk work; Opus verifies. |
| `audit` | Opus implements and verifies; a fresh Opus subagent reviews. |
| `full` | One Haiku or Sonnet implementer, Opus verification, then a fresh Opus review; exceptional only. |

## Quick start

You need a current Claude Code release with plugin and custom subagent support. Add the
repository marketplace and install the plugin from inside Claude Code:

~~~text
/plugin marketplace add SanHsien/agent-advisor
/plugin install agent-advisor-claude@agent-advisor
~~~

Start a fresh Opus session. Claude Code accepts the stable `opus` family alias and
resolves it to an allowed current model:

~~~sh
claude --model opus
~~~

Then use:

~~~text
Use /agent-advisor-claude:orchestration to build this feature and verify it. Declare the selective route before task tools.
~~~

Claude Code may substitute a model when an organization allowlist blocks a requested
family. If the session reports substitution for a selected Haiku, Sonnet, or Opus
lane, that lane stops instead of silently accepting different routing.

## Persistent activation

Installing the plugin puts the skill on the shelf; it does not make routing the default.
`orchestration` is invoked on demand, like any other skill. To make "declare a SELECTIVE
ROUTE before starting work" the standing behaviour of every session, paste
[`templates/claude-md-snippet.md`](templates/claude-md-snippet.md) into `~/.claude/CLAUDE.md`
— that file is loaded into every session, so no hook is required.

[`docs/ACTIVATION.zh-TW.md`](docs/ACTIVATION.zh-TW.md) covers the full setup: the Opus
model and `effortLevel` prerequisite, an optional `SessionStart` hook fallback, manual
installation for entrypoints where the `/plugin` panel cannot open, and which sessions a
change actually reaches. It also documents three traps that make a correct setup look
broken — a running session writing `effortLevel` back, a launcher `--model` flag
overriding `settings.json`, and `CLAUDE_CODE_EFFORT_LEVEL` locking a session.

Ready-to-copy files live in [`templates/`](templates/README.md).

## Local development

Run the plugin directly without installing it:

~~~sh
claude --model opus --plugin-dir ./claude/plugins/agent-advisor-claude
~~~

Validate the marketplace, plugin, agents, and routing contract:

~~~powershell
pwsh -NoProfile -File claude/scripts/verify.ps1
~~~

~~~sh
sh claude/scripts/verify.sh
~~~

See [the Traditional Chinese workflow](docs/WORKFLOW.zh-TW.md), [the activation
guide](docs/ACTIVATION.zh-TW.md), and the plugin's
[native operations reference](plugins/agent-advisor-claude/skills/orchestration/references/operations.md).

## Design differences from the Codex edition

- Agents use Claude Code Markdown frontmatter and the `haiku`, `sonnet`, and `opus`
  aliases, not Codex TOML profiles or GPT model IDs.
- Marketplace installation automatically registers plugin subagents; no companion
  agent-profile installer is needed.
- Claude plugin subagents cannot enforce `permissionMode` from plugin frontmatter.
  The reviewer therefore uses a restricted tool allowlist, an explicit no-mutation
  contract, and parent-side before/after repository checks.
- The Codex-only primary-attestation inspector is intentionally absent. Claude
  Advisor relies on observed session/model information and fails closed when a
  required model family cannot be established.
