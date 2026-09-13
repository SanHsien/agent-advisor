# Claude Code role contracts

Use these contracts with Agent Advisor for Claude Code's plugin-scoped subagents. The primary agent
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

- Haiku implementer: bounded, fully specified, low-ambiguity work.
- Sonnet implementer: judgment-heavy, high-risk, context-heavy, or broad changes.
- Opus reviewer: fresh review only after primary verification in `audit` or `full`.

If a Haiku result reveals genuine complexity or risk, the primary may declare an
escalation and issue one corrected complete packet to Sonnet. A corrected Haiku retry
is for a specification mistake; it is not a prerequisite for Sonnet.

## Review packet

Provide the reviewer with the user outcome, changed-file scope, important interfaces,
actual accumulated diff, and verification evidence. Require behavioral read-only
operation and exactly one verdict: `ship`, `fix-first`, or `rethink`.
