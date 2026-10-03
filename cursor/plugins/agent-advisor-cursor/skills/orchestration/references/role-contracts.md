# Cursor role contracts

Use these contracts with Agent Advisor for Cursor's subagents. The primary agent
settles architecture and supplies a complete packet before delegation.

## Implementation packet

~~~text
OBJECTIVE
<Observable outcome and why it matters.>

FILES AND OWNERSHIP
You own only:
- <exact file or module>

You are not alone in the codebase. Preserve concurrent edits, do not revert unrelated
work, and do not modify files outside this ownership.

INTERFACES
- <Signatures, schemas, commands, or behavior that must remain compatible.>

CONSTRAINTS
- <Repository conventions, safety boundaries, excluded scope, and settled decisions.>

VERIFICATION
- Run: <exact command>
  Success: <concrete expected result>
- Inspect: <exact file, diff, or artifact>
  Success: <concrete evidence>

RETURN
Return exact commands and actual evidence. A completion claim without evidence is invalid.

IMPLEMENTATION REPORT
STATUS: complete | partial | blocked
OBJECTIVE: <one-line restatement>
CHANGES: <file-by-file summary from the actual diff>
VERIFIED: <exact commands plus concrete output evidence>
JUDGMENT CALLS: <decisions left open by the packet, or none>
GAPS: <unfinished work, ambiguity, or none>
~~~

## Lane selection

- Sonnet implementer (`claude-sonnet-5-5-medium`): the default delegate lane for
  well-specified implementation, docs, slides, and spreadsheets.
- Sonnet deep implementer (`claude-sonnet-5-5-high`): debugging with an unclear root
  cause, changes across many files, or judgment-heavy, high-risk, context-heavy, or
  wide-blast-radius work.
- Composer implementer: mechanical batches only, such as renames, formatting, grep
  summaries, or applying an already-proven template.
- Opus reviewer: fresh review only after primary verification in `audit` or `full`.

Escalation ladder: Composer, then Sonnet implementer, then Sonnet deep implementer. If a
lane's result reveals genuine complexity or risk, the primary may declare an escalation
and issue one corrected complete packet to the next lane up. A corrected retry in the
same lane is for a specification mistake; it is not a prerequisite for escalating. Past
the deep implementer the primary decides how to proceed, and never silently switches
model.

## Throttled lane return

If a selected worker can report before stopping on an explicit provider rate limit,
return this compact availability report instead of presenting throttling as a code
failure:

~~~text
LANE AVAILABILITY REPORT
STATUS: throttled
ROLE: <exact selected agent/model ID>
CHECKPOINT: <last durable checkpoint or none>
STATE: <working-tree or artifact state>
RETRY: initial | confirmation
NEXT: back off and resume the same role/specification/ownership
~~~

If the worker cannot return, the primary may derive `throttled` only from an explicit
provider error. It must inspect durable state and confirm that no same-ownership worker
is active before scheduling or resuming the lane.

## Review packet

Provide the reviewer with the user outcome, changed-file scope, important interfaces,
actual accumulated diff, and verification evidence. Require behavioral read-only
operation and exactly one verdict: `ship`, `fix-first`, or `rethink`.
