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

## Termination and salvage

An auxiliary can stop before it finishes, and how much survives depends entirely on the
stop reason. Measured on 2026-09-04, both within one session:

| Stop reason | Report text | Files it already wrote | Salvageable |
| --- | --- | --- | --- |
| Turn limit reached | Returned, marked partial | Still in the working tree | Yes — read `git status` / `git diff` and take over |
| API rate limit (HTTP 429) | None, only a failure line | Nothing, if it had not written yet | No — the task output file was 0 bytes and the repository was unchanged |

The reasoning tokens are gone either way. What separates a recoverable stop from a total
loss is whether the auxiliary had already put something on disk. So:

1. **Every implementation prompt must require incremental landing.** State that the
   auxiliary writes each finished piece to its target file as it goes, instead of
   accumulating everything for one final report. This is the only measure that covers
   both stop reasons.
2. **Size the task to the turn budget.** Split per-item review work into batches, and
   instruct the auxiliary to stop early and report honestly where it stopped and what
   watermark that implies. A correct partial result beats a skimmed complete one.
3. **Near a usage limit, do not delegate long work.** Run it in the primary session,
   where every step is already visible in the transcript and an interruption still
   leaves the progress readable.
4. **Do not respawn a dead auxiliary verbatim.** Inspect the working tree first; taking
   over half-finished work is cheaper than repeating it.

A `SubagentStop` hook can flush unwritten state, but that is mitigation. Rule 1 is the fix.

## Rate-limit recovery

Treat an explicit provider `429 / Too Many Requests` or equivalent rate-limit as
unavailability of the selected lane, not as an implementation failure or a reason to
change the declared route.

1. Capture the provider error, selected role, current checkpoint, working-tree or
   artifact state, and remaining verification before retrying.
2. Confirm that no worker for the same ownership is still active.
3. After one short bounded backoff, make at most one confirmation retry.
4. If throttling repeats, stop immediate retries. Do not respawn a duplicate worker,
   accept a model substitution, or have the primary redo delegated work.
5. If persistent work was requested and scheduling is available, retry at low
   frequency (normally 15-30 minutes), remain quiet while state is unchanged, and use
   a known provider reset time when one exists. Otherwise report the lane unavailable.
6. Before resuming, inspect current state again and continue with the same role,
   specification, ownership, checkpoint, and verification plan.

Account-level remaining usage is not proof that one model lane is available. The
lane-specific rate-limit response is authoritative until a later attempt succeeds.

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
