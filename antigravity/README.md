# Agent Advisor for Antigravity

Agent Advisor for Antigravity is the Antigravity edition of
[Agent Advisor](https://github.com/SanHsien/agent-advisor). It adapts the selective
routing design of Daniel McAteer's upstream project to Antigravity's native plugin
bundle — a skill, custom subagents, and an always-active rule. It does not run Codex,
Claude Code, or Cursor, and it does not translate their configuration at runtime.

The primary session owns architecture, route selection, verification, and final
acceptance. It stays `solo` by default and uses one subagent only when the task risk
justifies it:

| Route | Native Antigravity delivery |
| --- | --- |
| `solo` | The primary agent plans, implements, tests, and self-reviews. |
| `delegate` | The flash lane handles bounded work or the pro lane handles judgment-heavy/high-risk work; the primary verifies. |
| `audit` | The primary implements and verifies; a fresh pro subagent reviews. |
| `full` | One flash or pro implementer, primary verification, then a fresh pro review; exceptional only. |

## Quick start

You need the Antigravity CLI (`agy`) or the Antigravity IDE with plugin support.

~~~sh
git clone https://github.com/SanHsien/agent-advisor
agy plugin install ./agent-advisor/antigravity/plugins/agent-advisor-antigravity
agy plugin list
~~~

Installation stages the bundle at `~/.gemini/config/plugins/agent-advisor-antigravity/`.
Start a session on a pro-tier model at high effort:

~~~sh
agy --model gemini-3.1-pro-high --effort high
~~~

The bundled rule requests the route declaration on its own, so naming the skill is
optional:

~~~text
Use the orchestration skill to build this feature and verify it. Declare the selective route before task tools.
~~~

## Persistent activation

`rules/selective-routing.md` ships inside the plugin. Plugin rules join the active rule
set when the plugin is enabled, so route declaration becomes standing behaviour without
editing `GEMINI.md` or `AGENTS.md`.

Worth knowing before debugging a rule that seems absent: the installer's component
summary lists skills and agents but not rules. It still copies the whole bundle —
`rules/` included — into `~/.gemini/config/plugins/<name>/`, and that directory is a
global customization root, so the rule is discovered from there.

If a session shows no sign of it, paste
[`templates/AGENTS.md.snippet.md`](templates/AGENTS.md.snippet.md) into the workspace
`AGENTS.md` or `GEMINI.md` instead.

## Local development

Validate against Antigravity's own checker and this repository's verifier:

~~~sh
agy plugin validate antigravity/plugins/agent-advisor-antigravity
sh antigravity/scripts/verify.sh
~~~

~~~powershell
pwsh -NoProfile -File antigravity/scripts/verify.ps1
~~~

See [the Traditional Chinese workflow](docs/WORKFLOW.zh-TW.md).

## Design differences from the other editions

- Subagent `model` takes a tier — `inherit`, `flash`, or `pro` — not a dated model ID.
  Lanes stay stable across model releases, unlike the Cursor edition's pinned IDs.
- Reasoning effort is separate from the tier: model IDs carry an effort suffix and the
  CLI accepts `--effort low|medium|high`.
- The reviewer ships no `tools` allowlist. The frontmatter field exists, but the
  tool-name vocabulary it expects is not part of the published customization
  documentation, and a guessed identifier would silently widen or empty the lane's
  permissions. Isolation rests on `commandExecutionPolicy: off`, the prompt contract,
  and the parent-side before/after check.
- Activation ships inside the plugin, as in the Cursor edition; the Claude Code edition
  needs a user-level `CLAUDE.md` edit instead.
- Hook commands are split into argv by Antigravity rather than passed to a shell, so a
  hook script path must be written bare. Claude Code passes hook commands to a shell,
  where the quoted form is correct. See [the hook quoting trap](#the-hook-quoting-trap).

## The hook quoting trap

This plugin ships no hooks, but anyone who adds one to Antigravity will meet this.

Antigravity splits a hook command into argv itself instead of handing it to a shell, so a
quoted path keeps its quote characters inside the filename and the interpreter fails with
`[Errno 22] Invalid argument`. Because `PreToolUse` hooks run *before* the tool does,
every guarded tool call then fails — including the ones an agent would need to repair the
file. The failure mode is an agent stuck asking a human to fix the config, because the
tools it would use to fix it are exactly the ones the broken hook is blocking.

~~~json
"command": "python \"C:\\Users\\<you>\\hooks\\guard.py\""   // fails
"command": "python C:\\Users\\<you>\\hooks\\guard.py"       // correct
~~~

With no shell to strip quotes there is also no way to express a path containing spaces,
so keep hook scripts on a space-free path.

Correctly shaped blocks: [`templates/hooks-example.json`](templates/hooks-example.json).
To repair a file that already has the quoted form:

~~~sh
python antigravity/scripts/fix_hook_quoting.py            # dry run
python antigravity/scripts/fix_hook_quoting.py --apply    # backs up, rewrites, re-parses
~~~

Prefer that over a one-line regex over the raw text. Every path in this file is dense
with escaped backslashes; a pattern that misses leaves the hook config unparseable, which
is harder to diagnose than the `Errno 22` it was meant to fix.
