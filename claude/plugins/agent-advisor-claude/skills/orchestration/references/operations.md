# Native Claude Code operations

Agent Advisor for Claude Code uses Claude Code's plugin skills and plugin-scoped Markdown subagents.
It never launches a nested CLI process as an agent.

## Model and agent mapping

| Agent | Family alias | Route |
| --- | --- | --- |
| Primary session | `opus` | all routes |
| `agent-advisor-claude:advisor-haiku-implementer` | `haiku` | bounded `delegate` or `full` |
| `agent-advisor-claude:advisor-sonnet-implementer` | `sonnet` | complex/high-risk `delegate` or `full` |
| `agent-advisor-claude:advisor-opus-reviewer` | `opus` | `audit` or `full` |

Start the primary session with `claude --model opus`. Model aliases deliberately avoid
pinning a dated model ID. Claude Code resolves aliases through the active provider and
organization allowlist; a visible substitution warning is a routing failure, not an
acceptable fallback.

## Availability preflight

Use Claude Code's agent listing UI to confirm only the role selected by the declared
route. Plugin agents appear with the `agent-advisor-claude:` namespace. Do not preflight or
spawn unused roles. If a selected role is missing, reload or reinstall the plugin once;
if it remains missing, stop that lane.

## Reviewer isolation

Claude Code ignores `permissionMode` in plugin agent frontmatter, so this plugin does
not claim hard read-only sandboxing. The reviewer definition has no Edit or Write tool
and explicitly prohibits mutating shell commands. The primary must also:

1. Record `git status --short` and relevant artifact hashes before review.
2. Spawn one fresh Opus reviewer with the review packet.
3. Record the same state after review.
4. Reject the review if any repository or artifact state changed.

## Validation

From the repository root:

~~~powershell
pwsh -NoProfile -File claude/scripts/verify.ps1
~~~

~~~sh
sh claude/scripts/verify.sh
~~~

When the installed Claude Code version supports it, also run:

~~~sh
claude plugin validate claude
claude plugin validate claude/plugins/agent-advisor-claude/agents
~~~

The repository verifier checks marketplace and manifest JSON, exact agent inventory,
model aliases, reviewer restrictions, route declarations, documentation links, and
absence of Codex-specific runtime contracts inside the Claude implementation.
