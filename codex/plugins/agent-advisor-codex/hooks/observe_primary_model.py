#!/usr/bin/env python3
"""Advisory UserPromptSubmit hook: report the active primary model, nothing else.

Why this exists
---------------
The primary session is the one piece of routing evidence the plugin cannot inspect
for itself. `inspect-agent-runtime` reads an auxiliary's rollout; the primary's own
model and effort are, in the general case, unobservable from inside the session, so
the gate falls back to a user-level standing attestation and labels the result
`operator-attested`, not `runtime-verified`.

If the host hands a hook the active model, that one field can stop being attested
and start being observed. This hook does exactly that much and no more.

What it deliberately does not do
--------------------------------
- It never blocks. Every unexpected input path exits 0 with no output, so a host
  that does not supply `model` (or supplies a payload shaped differently than
  expected) costs nothing and changes nothing.
- It never claims reasoning effort. Hook input exposes the model; it does not
  expose effort, and an advisory that implied otherwise would weaken the gate it
  is meant to strengthen.
- It never changes a model or authorizes orchestration. The gate in
  `skills/orchestration/SKILL.md` remains the authority.

Fork note: upstream's version (DannyMac180/sol-advisor PR #26) is a shell script
that shells out to `jq`. This fork is Windows-first and `jq` is not present on a
default Windows host, while `python3` is already a dependency of `verify.sh`. The
behaviour is the same; the dependency is one this repo already carries.
"""

from __future__ import annotations

import json
import re
import sys

REQUIRED_MODEL = "gpt-5.6-sol"

# Codex currently ignores UserPromptSubmit matchers, so the allowlist is enforced
# here instead: the advisory belongs to an orchestration prompt, not to every
# prompt the user types.
_ORCHESTRATION_COMMAND = re.compile(
    r"(^|\s)\$agent-advisor-codex:orchestration(\s|$)"
)

# The model string is echoed into developer context. Bound it to a conservative
# charset so a hostile or malformed value cannot smuggle markup or control
# characters through the advisory line.
_SAFE_MODEL = re.compile(r"\A[A-Za-z0-9._-]{1,64}\Z")


def advisory_for(payload: object) -> str | None:
    """Return the advisory line for this payload, or None to stay silent."""
    if not isinstance(payload, dict):
        return None
    if payload.get("hook_event_name") != "UserPromptSubmit":
        return None

    prompt = payload.get("prompt")
    model = payload.get("model")
    if not isinstance(prompt, str) or not isinstance(model, str):
        return None
    if not _ORCHESTRATION_COMMAND.search(prompt):
        return None
    if not _SAFE_MODEL.match(model):
        return None

    if model == REQUIRED_MODEL:
        return (
            f"Agent Advisor model check: active model is {REQUIRED_MODEL}. "
            "This covers the model field only -- reasoning effort is not exposed to "
            "hooks, so complete the primary-session gate before orchestration."
        )
    return (
        f"Agent Advisor model mismatch: active model is {model}, but Agent Advisor "
        f"requires {REQUIRED_MODEL}. Select it with /model, confirm with /status, "
        "then complete the primary-session gate."
    )


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except (OSError, ValueError):
        return 0

    line = advisory_for(payload)
    if line:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
