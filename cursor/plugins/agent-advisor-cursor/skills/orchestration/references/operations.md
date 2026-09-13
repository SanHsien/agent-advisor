# Native Cursor operations

Agent Advisor for Cursor uses Cursor's plugin skills, subagents, and always-apply rules.
It never launches a nested CLI process as an agent.

## Model and agent mapping

| Agent | Model | Route |
| --- | --- | --- |
| Primary session | explicitly selected high-capability reasoning model | all routes |
| `advisor-composer-implementer` | `composer-2.5` | bounded `delegate` or `full` |
| `advisor-sonnet-implementer` | `claude-sonnet-5-thinking-high` | complex/high-risk `delegate` or `full` |
| `advisor-opus-reviewer` | `claude-opus-5-thinking-high` | `audit` or `full` |

Cursor has no stable family aliases, so each lane pins a model ID. The IDs above are a
snapshot; re-check them against the current catalog before editing a lane:

~~~sh
cursor-agent models
~~~

Cursor also accepts bracket parameters on a model ID, for example
`claude-opus-5[effort=high,context=300k]`, when a lane needs a specific effort level.

A pinned ID fails closed. If a lane's model is unavailable on the current plan, stop
that lane rather than letting Cursor fall back to a different model.

## Availability preflight

Confirm only the role selected by the declared route. Subagents resolve from
`.cursor/agents/` (project) and `~/.cursor/agents/` (user); plugin-provided agents are
registered when the plugin is installed and enabled. Do not preflight or spawn unused
roles. If a selected role is missing, reinstall or re-enable the plugin once; if it
remains missing, stop that lane.

## Reviewer isolation

`readonly: true` in the reviewer's frontmatter is enforced by Cursor at the runtime
level, so the review lane does not depend on prompt discipline alone. The prompt still
prohibits mutating shell commands, and the primary must also:

1. Record `git status --short` and relevant artifact hashes before review.
2. Spawn one fresh reviewer with the review packet.
3. Record the same state after review.
4. Reject the review if any repository or artifact state changed.

## Always-apply rule

`rules/selective-routing.mdc` ships inside this plugin with `alwaysApply: true`, so an
installed plugin makes route declaration standing behaviour. No edit to a user-level
context file is required.

## Validation

From the repository root:

~~~powershell
pwsh -NoProfile -File cursor/scripts/verify.ps1
~~~

~~~sh
sh cursor/scripts/verify.sh
~~~

The repository verifier checks manifest JSON, exact agent inventory, pinned models, the
reviewer's `readonly` flag, the always-apply rule, route declarations, documentation
links, and the absence of Codex or Claude runtime contracts inside the Cursor
implementation.
