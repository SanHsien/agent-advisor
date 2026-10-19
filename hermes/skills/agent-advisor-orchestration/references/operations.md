# Hermes Agent operations

This is the Hermes adaptation of Agent Advisor's termination-and-salvage guidance.
Hermes uses `delegate_task`; do not launch a nested agent CLI when delegation already provides the required isolation.

## Termination and salvage

An auxiliary can stop at a turn limit, provider rate limit, timeout, or parent interruption. Its final summary is not durable evidence by itself.

1. For multi-item or implementation work, require incremental writes to the workspace rather than accumulating all results for the final response.
2. Size delegated work to the available turn and token budget; batch large inventories and record a durable watermark.
3. Near a provider usage limit, keep long sequential work in the primary session.
4. After a child stops, inspect its transcript path and every claimed file/diff before deciding what survived.
5. Do not respawn the same task verbatim until the primary checks existing artifacts; take over valid partial work when cheaper.
6. Treat every child report as a claim. The primary still owns tests, verification, external-state read-back, and final acceptance.

A turn-limit stop may leave already-written files. A rate-limit stop can leave no report and no artifact if the child had not written yet. Incremental landing is the mitigation that covers both cases.

## Rate-limit recovery

Treat an explicit provider `429 / Too Many Requests` or equivalent rate-limit as lane
unavailability, not as a failed implementation or a reason to change the route.

1. Capture the provider error, selected role/provider/model/effort, durable checkpoint,
   workspace or artifact state, and remaining verification.
2. Confirm that no `delegate_task` with the same ownership is still active.
3. After one short bounded backoff, make at most one confirmation retry.
4. If throttling repeats, stop immediate retries. Do not dispatch a duplicate task,
   silently switch provider/model/role/effort, or have the primary redo delegated work.
5. If persistent work and scheduling were already authorized, retry at low frequency
   (normally 15-30 minutes), remain silent while state is unchanged, and prefer a known
   provider reset time. Do not create or modify cron solely because throttling occurred.
6. Before resuming, inspect current state again and continue with the same role,
   specification, ownership, checkpoint, and verification plan.

Account-wide remaining usage is not proof that one provider/model lane is available.
The lane-specific rate-limit response remains authoritative until a later attempt
succeeds.

If a child can report before stopping, use:

```text
LANE AVAILABILITY REPORT
STATUS: throttled
ROLE: <exact role/provider/model/effort>
CHECKPOINT: <last durable checkpoint or none>
STATE: <workspace or artifact state>
RETRY: initial | confirmation
NEXT: back off and resume the same role/specification/ownership
```
