# Agent Advisor for Cursor

Agent Advisor for Cursor is the Cursor edition of
[Agent Advisor](https://github.com/SanHsien/agent-advisor). It adapts the selective
routing design of Daniel McAteer's upstream project to Cursor's native plugin format,
Markdown subagents, and always-apply rules; it does not run Codex or Claude Code, and it
does not translate their configuration at runtime.

The primary session owns architecture, route selection, verification, and final
acceptance. It stays `solo` by default and uses one auxiliary only when the task risk
justifies it:

| Route | Native Cursor delivery |
| --- | --- |
| `solo` | The primary agent plans, implements, tests, and self-reviews. |
| `delegate` | Composer handles bounded work or Sonnet handles judgment-heavy/high-risk work; the primary verifies. |
| `audit` | The primary implements and verifies; a fresh Opus subagent reviews. |
| `full` | One Composer or Sonnet implementer, primary verification, then a fresh Opus review; exceptional only. |

## Quick start

You need a Cursor release with plugin, subagent, and rule support.

Install from the **Customize** panel in the sidebar: find the plugin, select **Install**,
and choose project or user scope.

To install from this repository without going through the marketplace, place the plugin
directory in Cursor's local plugin folder — a directory copy or a symlink both work:

~~~powershell
$dst = "$env:USERPROFILE\.cursor\plugins\local\agent-advisor-cursor"
New-Item -ItemType SymbolicLink -Path $dst -Target (Resolve-Path .\cursor\plugins\agent-advisor-cursor)
~~~

~~~sh
ln -s "$PWD/cursor/plugins/agent-advisor-cursor" ~/.cursor/plugins/local/agent-advisor-cursor
~~~

Then select a high-capability reasoning model — not `auto`, which may resolve to a fast
model mid-session — and start work. The bundled always-apply rule requests the route
declaration on its own; naming the skill is optional:

~~~text
Use the orchestration skill to build this feature and verify it. Declare the selective route before task tools.
~~~

## Persistent activation

Unlike editions that need a user-level context file, this one ships its own activation.
`rules/selective-routing.mdc` has `alwaysApply: true`, so installing and enabling the
plugin makes route declaration standing behaviour in every session — nothing to paste
into `AGENTS.md` or user rules.

The rule states the requirement and the default; the skill carries the full contract and
loads on demand. See [the Traditional Chinese workflow](docs/WORKFLOW.zh-TW.md).

## Local development

Validate the manifest, agents, rule, and routing contract:

~~~powershell
pwsh -NoProfile -File cursor/scripts/verify.ps1
~~~

~~~sh
sh cursor/scripts/verify.sh
~~~

## Design differences from the other editions

- Cursor subagent frontmatter supports `name`, `description`, `model`, `readonly`, and
  `is_background`. There is no tool allowlist, so lane isolation comes from `readonly`
  rather than from a restricted tool set.
- `readonly: true` is enforced by Cursor at runtime, so the reviewer lane does not rely
  on prompt discipline alone the way the Claude Code edition must.
- Cursor has no stable model family aliases. Each lane pins a model ID from
  `cursor-agent models`, which fails closed when a model is unavailable rather than
  silently substituting a different one.
- Activation ships inside the plugin as an always-apply rule; no user-level context file
  is edited.
