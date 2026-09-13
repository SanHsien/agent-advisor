---
name: orchestration
description: >-
  Antigravity-native risk-gated selective routing. Use when starting any non-trivial
  implementation, refactor, or debugging task to choose between default solo delivery,
  targeted flash or pro delegation, and a fresh pro review only when justified.
---

# Agent Advisor for Antigravity Orchestration

Act as the architect. Own the user's intent, architecture, route choice,
implementation or delegation, verification, escalation decisions, and final
acceptance. Use exactly four modes: `solo`, `delegate`, `audit`, and `full`.

Read [references/operations.md](references/operations.md) for native Antigravity runtime
rules. Before any delegation, also read
[references/role-contracts.md](references/role-contracts.md).

## Confirm the primary session

Run the primary session on a pro-tier model at high reasoning effort. Antigravity exposes
effort both as a model suffix and as the `--effort` flag, so confirm the effective
setting rather than assuming a default.

The observed session model is authoritative. If it cannot be observed, ask the user once
instead of inferring it from settings, plugin files, or environment defaults.

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

The bundled `rules/selective-routing.md` applies this requirement to every session in
which the plugin is enabled, so the declaration is expected even when the user did not
name this skill.

## Route contracts

- `solo`: the primary agent plans, implements, tests, and self-reviews. Invoke no subagent.
- `delegate`: invoke `advisor-flash-implementer` for bounded, fully specified work or
  `advisor-pro-implementer` for judgment-heavy, high-risk, context-heavy, or
  wide-blast-radius work. The primary verifies and does not add a fresh reviewer.
- `audit`: primary implements and verifies, then one fresh `advisor-pro-reviewer`
  inspects the accumulated diff.
- `full`: exceptional only. Use one selected implementer, primary verification, and
  then one fresh reviewer.

Subagent work substitutes for primary implementation; it must not duplicate it.
One subagent is the default maximum. `full` is the explicit exception.

## Preflight and runtime evidence

Preflight only agents selected by the route. Confirm the exact subagent is available
before invoking it. Antigravity subagents run as independent concurrent sessions, so the
primary must collect their evidence explicitly rather than assuming shared context.

## Worker and review flow

Every implementation prompt must include OBJECTIVE, FILES AND OWNERSHIP, INTERFACES,
CONSTRAINTS, VERIFICATION, RETURN, and the structured IMPLEMENTATION REPORT defined in
[role-contracts.md](references/role-contracts.md). State exact owned files, preserve
concurrent edits, and never widen scope silently.

Treat worker reports as claims. The primary inspects the complete diff and reruns all
requested checks. For `audit` or `full`, the reviewer returns `ship`, `fix-first`, or
`rethink` and never implements fixes. Any correction invalidates the prior verdict and
requires verification plus a new fresh review.
