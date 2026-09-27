# Native Antigravity operations

Agent Advisor for Antigravity uses Antigravity's plugin bundle: a skill, custom subagents,
and an always-active rule. It never launches a nested CLI process as an agent.

## Model and agent mapping

| Agent | Model tier | Route |
| --- | --- | --- |
| Primary session | pro tier at high effort | all routes |
| `advisor-flash-implementer` | `flash` | bounded `delegate` or `full` |
| `advisor-pro-implementer` | `pro` | complex/high-risk `delegate` or `full` |
| `advisor-pro-reviewer` | `pro` | `audit` or `full` |

Antigravity's subagent `model` field takes a tier — `inherit`, `flash`, or `pro` — not a
dated model ID. The tier resolves through the account's model catalog, which keeps the
lanes stable across model releases. Check what a tier currently resolves to with:

~~~sh
agy models
~~~

Reasoning effort is separate from the tier. Model IDs carry an effort suffix and the CLI
also accepts `--effort low|medium|high`; confirm the effective value instead of assuming
a default.

## Availability preflight

Confirm only the role selected by the declared route. Subagents resolve from
`.agents/agents/` (workspace), `~/.gemini/config/agents/` (global), and
`plugins/<name>/agents/` (plugin). Do not preflight or invoke unused roles. If a selected
role is missing, re-enable or reinstall the plugin once; if it remains missing, stop that
lane.

## Rate-limit recovery

Treat an explicit provider `429 / Too Many Requests` or equivalent rate-limit as
unavailability of the selected lane, not as an implementation failure or a reason to
change the declared route.

1. Capture the provider error, selected role, current checkpoint, working-tree or
   artifact state, and remaining verification before retrying.
2. Confirm that no subagent session for the same ownership is still active.
3. After one short bounded backoff, make at most one confirmation retry.
4. If throttling repeats, stop immediate retries. Do not invoke a duplicate session,
   substitute another subagent/model tier, or have the primary redo delegated work.
5. If persistent work was requested and scheduling is available, retry at low
   frequency (normally 15-30 minutes), remain quiet while state is unchanged, and use
   a known provider reset time when one exists. Otherwise report the lane unavailable.
6. Before resuming, inspect current state again and continue with the same role,
   specification, ownership, checkpoint, and verification plan.

Account-level remaining usage is not proof that one model lane is available. The
lane-specific rate-limit response is authoritative until a later attempt succeeds.

## Reviewer isolation

`commandExecutionPolicy: off` denies the reviewer shell execution. The remaining
read-only guarantee is behavioral: the reviewer prompt prohibits any mutation, and the
primary must also:

1. Record `git status --short` and relevant artifact hashes before review.
2. Invoke one fresh reviewer with the review packet.
3. Record the same state after review.
4. Reject the review if any repository or artifact state changed.

The reviewer deliberately ships no `tools` allowlist. The frontmatter field exists, but
the tool-name vocabulary it expects is not part of the published customization
documentation, and a guessed identifier would silently widen or empty the lane's
permissions. Isolation therefore rests on the execution policy, the prompt contract, and
the parent-side before/after check.

## Always-active rule

`rules/selective-routing.md` ships inside this plugin. Plugin rules are merged into the
active rule set whenever the plugin is enabled, so an installed plugin makes route
declaration standing behaviour without an edit to `GEMINI.md` or `AGENTS.md`.

One observed detail worth knowing before debugging a missing rule: `agy plugin install`
prints a component summary that enumerates skills, agents, commands, MCP servers, and
hooks — rules are not listed, and `agy plugin list` reports `components` as
`["skills","agents"]` for this bundle. That summary is not the whole story. The installer
copies the entire bundle, `rules/` included, into `~/.gemini/config/plugins/<name>/`,
and `~/.gemini/config/` is itself a global customization root, so the rule is discovered
from there.

If a session shows no sign of the rule, the fallback is the same text in `AGENTS.md` or
`GEMINI.md` at the workspace root — see the activation guide.

## Workspace discovery note

Antigravity discovers workspace customizations under `.agents/` walking up from the
current directory. This repository's root `.agents/plugins/marketplace.json` is a Codex
discovery catalog, not an Antigravity plugin: it has no `plugin.json`, so Antigravity
ignores it. Keep it that way — do not add a `plugin.json` beside it.

## Validation

From the repository root:

~~~powershell
pwsh -NoProfile -File antigravity/scripts/verify.ps1
~~~

~~~sh
sh antigravity/scripts/verify.sh
~~~

With the CLI installed, also validate the bundle against Antigravity's own checker:

~~~sh
agy plugin validate antigravity/plugins/agent-advisor-antigravity
~~~
