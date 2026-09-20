---
name: orchestration
description: "Claude Code-native risk-gated selective routing: default solo delivery, targeted Haiku or Sonnet delegation, and fresh Opus review only when justified."
---

# Agent Advisor for Claude Code Orchestration

Act as the architect. Own the user's intent, architecture, route choice,
implementation or delegation, verification, escalation decisions, and final
acceptance. Use exactly four modes: `solo`, `delegate`, `audit`, and `full`.

Read [references/operations.md](references/operations.md) for native Claude Code
runtime rules. Before any delegation, also read
[references/role-contracts.md](references/role-contracts.md).

## Confirm the primary session

Run the primary Claude Code session on the `opus` model family. Observed session
metadata and Claude Code model-substitution warnings are authoritative. If the
observed primary model is not Opus, stop substantive work. If the model family is
unobservable, ask the user once instead of inferring it from settings, plugin files,
or environment defaults.

## Declare the route before task tools

Before the first task tool call, emit exactly:

~~~text
SELECTIVE ROUTE
mode: solo | delegate | audit | full
risk: <concise, task-specific rationale>
~~~

Choose `solo` unless a concrete risk or complete specification makes an auxiliary
materially useful. A later declaration may only escalate after newly observed risk;
never silently downgrade.

## Provider throttling is lane unavailability

A provider `429 / Too Many Requests` or equivalent explicit rate-limit response is a
lane-availability failure, not an implementation finding and not evidence that the
risk classification changed.

- Preserve the exact checkpoint, working-tree state, role, specification, ownership,
  and verification plan before any retry.
- After one short bounded backoff, allow at most one confirmation retry. Do not open
  parallel duplicate workers or enter an immediate retry loop.
- Repeated throttling stops the selected lane. Never silently downgrade, substitute
  another role/model family, or let the primary duplicate delegated implementation.
- Account-level remaining usage does not prove that a specific provider/model lane is
  available; the lane-specific rate-limit response remains authoritative.
- When persistent work was requested and scheduling is available, use a low-frequency
  retry or heartbeat, stay quiet while state is unchanged, and resume with the same
  role, specification, ownership, and verification plan. Otherwise report the lane
  unavailable and resume later.

## Route contracts

- `solo`: primary Opus plans, implements, tests, and self-reviews. Spawn no auxiliary.
- `delegate`: select `agent-advisor-claude:advisor-haiku-implementer` for bounded, fully
  specified work or `agent-advisor-claude:advisor-sonnet-implementer` for judgment-heavy,
  high-risk, context-heavy, or wide-blast-radius work. The primary verifies and does
  not add a fresh reviewer.
- `audit`: primary implements and verifies, then one fresh
  `agent-advisor-claude:advisor-opus-reviewer` inspects the accumulated diff.
- `full`: exceptional only. Use one selected implementer, primary verification, and
  then one fresh Opus reviewer.

Auxiliary work substitutes for primary implementation; it must not duplicate it.
One auxiliary is the default maximum. `full` is the explicit exception.

## Preflight and runtime evidence

Preflight only agents selected by the route. Confirm the exact plugin-scoped agent is
available before spawning it. After spawn, treat any Claude Code substitution warning
or evidence of a different family as a hard stop for that lane. Never silently replace
Haiku, Sonnet, or Opus with another model family.

Claude Code ignores `permissionMode` on plugin subagents. For review, capture
`git status --short` and any relevant artifact hashes before and after the reviewer.
The reviewer is valid only when its restricted tool set and the observed repository
state show no mutation.

## Worker and review flow

Every implementation prompt must include OBJECTIVE, FILES AND OWNERSHIP, INTERFACES,
CONSTRAINTS, VERIFICATION, RETURN, and the structured IMPLEMENTATION REPORT defined in
[role-contracts.md](references/role-contracts.md). State exact owned files, preserve
concurrent edits, and never widen scope silently.

Treat worker reports as claims. The primary inspects the complete diff and reruns all
requested checks. For `audit` or `full`, the reviewer returns `ship`, `fix-first`, or
`rethink` and never implements fixes. Any correction invalidates the prior verdict and
requires verification plus a new fresh review.
