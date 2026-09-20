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

## Rate-limit recovery

Treat an explicit provider `429 / Too Many Requests` or equivalent rate-limit as
unavailability of the selected lane, not as an implementation failure or a reason to
change the declared route.

1. Capture the provider error, selected role, current checkpoint, working-tree or
   artifact state, and remaining verification before retrying.
2. Confirm that no worker for the same ownership is still active.
3. After one short bounded backoff, make at most one confirmation retry.
4. If throttling repeats, stop immediate retries. Do not spawn a duplicate worker,
   substitute another agent/model ID, or have the primary redo delegated work.
5. If persistent work was requested and scheduling is available, retry at low
   frequency (normally 15-30 minutes), remain quiet while state is unchanged, and use
   a known provider reset time when one exists. Otherwise report the lane unavailable.
6. Before resuming, inspect current state again and continue with the same role,
   specification, ownership, checkpoint, and verification plan.

Account-level remaining usage is not proof that one model lane is available. The
lane-specific rate-limit response is authoritative until a later attempt succeeds.

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
