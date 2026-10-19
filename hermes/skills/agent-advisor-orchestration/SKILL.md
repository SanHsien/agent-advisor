---
name: agent-advisor-orchestration
description: Use when routing non-trivial Hermes coding work by risk.
version: 1.4.0
author: SanHsien/agent-advisor (Hermes adaptation)
license: MIT
metadata:
  hermes:
    tags: [routing, delegation, review, governance]
---

# Agent Advisor — Hermes Orchestration

## When to Use

Use for non-trivial implementation, refactoring, debugging, review, or multi-workstream coding tasks. Skip for simple questions and status lookups.

Own intent, architecture, route choice, verification, and final acceptance. Use exactly four modes: `solo`, `delegate`, `audit`, `full`.

Before delegating, read [references/operations.md](references/operations.md). Require incremental file landing for implementation work so a stopped auxiliary can leave salvageable progress; after interruption, inspect workspace state before deciding whether to take over or retry.

Before the first task tool call on non-trivial coding work, emit:

```text
SELECTIVE ROUTE
mode: solo | delegate | audit | full
risk: <concise, task-specific rationale>
```

The enabled `governance-autoapply` Hermes plugin enforces this per turn before mutating file/configuration tools. If a call is blocked, emit the declaration and retry; do not disable or bypass the guard.

- `solo`: default. Primary implements, tests, and self-reviews.
- `delegate`: use `delegate_task` only for a bounded implementation or a materially useful independent workstream. Primary verifies all claims.
- `audit`: primary implements and verifies, then a fresh `delegate_task` reviewer inspects the accumulated diff without modifying it.
- `full`: exceptional; one implementer plus one fresh reviewer. Do not duplicate the primary's work.

Rules:
1. Escalate only when observed risk justifies it; never silently downgrade.
2. Child reports are claims. Re-read files, diffs, tests, and external state yourself.
3. One auxiliary is the default maximum; `full` is the explicit exception.
4. Delegation never transfers user intent, architecture, security decisions, or final acceptance.
5. Do not delegate tasks requiring user interaction, credentials, or destructive approval.

## Provider throttling is lane unavailability

A provider `429 / Too Many Requests` or equivalent explicit rate-limit response means
the selected lane is temporarily unavailable. It is not an implementation finding and
does not change the route's risk classification.

- Preserve the exact checkpoint, workspace state, role, specification, ownership, and
  verification plan before any retry.
- After one short bounded backoff, allow at most one confirmation retry. Do not open a
  parallel duplicate `delegate_task` or enter an immediate retry loop.
- Repeated throttling stops the selected lane. Never silently change provider, model,
  role, or reasoning effort, and do not let the primary duplicate delegated work.
- Account-level remaining usage does not prove that a specific provider/model lane is
  available; the lane-specific response is authoritative.
- When persistent work was requested, use Hermes cron only if that scheduling action is
  already authorized; retry at low frequency, stay silent while state is unchanged,
  and resume with the same role, specification, ownership, and verification plan.

## Primary and role evidence

Keep the explicitly selected primary model/provider and configured effort. Confirm
runtime evidence before delegation; configuration is not proof of an active child.
Hermes `delegate_task` inherits the parent model unless `delegation.model/provider`
is configured. Do not invent per-call model or effort overrides. The selected child
must substitute for primary implementation, not duplicate it. A review child is
fresh and behaviorally read-only; normal delegation tools do not provide a guaranteed
read-only sandbox. Check workspace state and artifact hashes before and after review.

## Cost-aware execution

Before delegation or verification, read [成本與驗收紀律](references/cost-policy.md).
No nested CLI agents, automatic advisor calls, new parallel defaults, or provider changes.
