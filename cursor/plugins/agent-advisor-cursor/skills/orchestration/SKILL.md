---
name: orchestration
description: "Cursor-native risk-gated selective routing: default solo delivery, targeted Composer or Sonnet delegation, and fresh Opus review only when justified."
---

# Agent Advisor for Cursor Orchestration

Act as the architect. Own the user's intent, architecture, route choice,
implementation or delegation, verification, escalation decisions, and final
acceptance. Use exactly four modes: `solo`, `delegate`, `audit`, and `full`.

Read [references/operations.md](references/operations.md) for native Cursor runtime
rules. Before any delegation, also read
[references/role-contracts.md](references/role-contracts.md).

## Confirm the primary session

Run the primary session on a high-capability reasoning model. Cursor's `auto` selection
is not one: it may resolve to a fast model mid-session, which silently removes the
reasoning the architect role depends on. Select the model explicitly.

The observed session model is authoritative. If it cannot be observed, ask the user
once instead of inferring it from settings, plugin files, or environment defaults.

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

The bundled `rules/selective-routing.mdc` applies this requirement to every session,
so the declaration is expected even when the user did not name this skill.

## Route contracts

- `solo`: the primary agent plans, implements, tests, and self-reviews. Spawn no auxiliary.
- `delegate`: select `advisor-composer-implementer` for bounded, fully specified work or
  `advisor-sonnet-implementer` for judgment-heavy, high-risk, context-heavy, or
  wide-blast-radius work. The primary verifies and does not add a fresh reviewer.
- `audit`: primary implements and verifies, then one fresh `advisor-opus-reviewer`
  inspects the accumulated diff.
- `full`: exceptional only. Use one selected implementer, primary verification, and
  then one fresh reviewer.

Auxiliary work substitutes for primary implementation; it must not duplicate it.
One auxiliary is the default maximum. `full` is the explicit exception.

## Preflight and runtime evidence

Preflight only agents selected by the route. Confirm the exact subagent is available
before spawning it. Cursor pins each lane to a model ID rather than a family alias, so
a lane whose model is unavailable on the current plan fails closed: stop that lane
instead of accepting a substitute.

## Worker and review flow

Every implementation prompt must include OBJECTIVE, FILES AND OWNERSHIP, INTERFACES,
CONSTRAINTS, VERIFICATION, RETURN, and the structured IMPLEMENTATION REPORT defined in
[role-contracts.md](references/role-contracts.md). State exact owned files, preserve
concurrent edits, and never widen scope silently.

Treat worker reports as claims. The primary inspects the complete diff and reruns all
requested checks. For `audit` or `full`, the reviewer returns `ship`, `fix-first`, or
`rethink` and never implements fixes. Any correction invalidates the prior verdict and
requires verification plus a new fresh review.
