# Native operations

This is the maintainer and operator reference for Agent Advisor for Codex's native custom-agent
workflow. Keep the README user-facing; use this page when installing, delegating,
inspecting routing, or validating a release.

## Role pins and spawn contract

The installed TOMLs are the source of truth:

| Role type | Model | Effort | Use |
|---|---|---|---|
| agent_advisor_codex_luna_implementer | gpt-5.6-luna | max | Delegate/full bounded routine implementation |
| agent_advisor_codex_terra_implementer | gpt-5.6-terra | high | Delegate/full judgment-heavy or high-risk implementation |
| agent_advisor_codex_sol_reviewer | gpt-5.6-sol | high | Audit/full fresh review; requests read-only sandbox |

Native spawn requests name the role and use a fresh context:

~~~text
agent_type: agent_advisor_codex_luna_implementer
fork_turns: none
~~~

Use the Terra type only when the selected delegate or full route needs it:

~~~text
agent_type: agent_advisor_codex_terra_implementer
fork_turns: none
~~~

Use a fresh Sol reviewer only for audit or full after parent verification:

~~~text
agent_type: agent_advisor_codex_sol_reviewer
fork_turns: none
~~~

Do not attach model or reasoning overrides. A missing, conflicting, unavailable, or
unobservable role/model/effort is a hard stop; never substitute another role.

## Selective route declaration, preflight, and caching

The primary session must be Sol / High. Observed primary runtime metadata is
authoritative and any conflict stops work. If one or both primary fields are
unobservable, the exact line
`AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION: gpt-5.6-sol/high` in active instructions is only a
candidate. Declare the route before task tools, then use the platform-specific bundled
inspector as the first and only preflight call:

~~~powershell
pwsh -NoProfile -File ..\..\scripts\inspect-primary-attestation.ps1
~~~

~~~sh
sh ../../scripts/inspect-primary-attestation.sh
~~~

Resolve these paths from this skill directory. The inspector fails closed unless the
actual regular user-level/global `AGENTS.md` contains exactly one marker, is bounded in
size, and has no user-level `AGENTS.override.md`. A project file cannot satisfy it.
Until it passes, use no other task tool, spawn no agent, and do no substantive work.
A pass attests only missing primary fields; label it operator-attested with verified
user-level provenance, do not ask again in every new task, and never let it override
observed metadata. Missing metadata without verified provenance or explicit
current-task confirmation remains a stop. Static `config.toml`, UI defaults, plugin
metadata, repo files, and companion role pins are not current-task evidence.

This standing attestation applies only to the primary session. Every selected
auxiliary still requires the exact task-scoped role/model/effort evidence below.
Companion installation is separate from task routing because plugin installation does
not register user-owned TOMLs.

At installation or update time, run the repository-relative installer and its exactness
check:

~~~sh
sh codex/plugins/agent-advisor-codex/scripts/install-agents.sh
sh codex/plugins/agent-advisor-codex/scripts/install-agents.sh --check
~~~

When operating from an installed skill, resolve the same script relative to this
reference's parent skill:

~~~sh
skill_dir=<directory-containing-this-SKILL.md>
installer="$skill_dir/../../scripts/install-agents.sh"
sh "$installer" --check
~~~

The installer is fail-closed and performs its own post-install exactness check. It
recognizes only byte-exact historical templates, including the shipped v0.2.0 profiles
and the v0.5.0 Luna/Terra profiles during a v0.5.1 update. Modified/unsafe/nonregular/
symlinked/conflicting destinations remain refusals, and all mutations are preflighted.

The root emits one machine-auditable declaration before its first task tool call:

~~~text
SELECTIVE ROUTE
mode: solo | delegate | audit | full
risk: <concise, task-specific rationale>
~~~

Solo is the default. One auxiliary is the default maximum; full is an explicit broad
or high-risk exception. The root may emit a later declaration only to escalate when
newly observed risk justifies it. It records that evidence and never silently
downgrades.

The existing --check flag verifies all three roles. For task-scoped preflight, check
only the auxiliaries selected by the declaration; every check is non-mutating and
fail-closed:

| Route | Required companion checks |
|---|---|
| solo | None |
| delegate (Luna) | `--check --check-role luna` |
| delegate (Terra) | `--check --check-role terra` |
| audit | `--check --check-role sol` |
| full (Luna) | `--check --check-role luna --check-role sol` |
| full (Terra) | `--check --check-role terra --check-role sol` |

For example:

~~~sh
sh codex/plugins/agent-advisor-codex/scripts/install-agents.sh --check --check-role luna
sh codex/plugins/agent-advisor-codex/scripts/install-agents.sh --check --check-role sol
~~~

Unknown or missing role arguments fail before any destination mutation. A selective
check ignores unselected role destinations, while the all-role --check behavior
remains unchanged. Cache successful checks only for the task; never carry them across
later tasks, installation/update, or routing/configuration changes.

Luna / Max is for bounded, fully specified work. Terra / High is selected for
judgment-heavy, high-risk, context-heavy, or wide-blast-radius work. A Luna result
may justify a declared Terra escalation only when it shows newly observed risk. One
corrected Luna attempt is reserved for a specification error and is not a prerequisite
for Terra.

If public metadata omits model or effort, use the local inspector below as a fallback
for those omitted fields only. Do not use it to replace available public evidence.

### Optional: the advisory model hook

The primary's model is the one field the plugin otherwise has to take on attestation.
If the host exposes the active model to hooks, that field can be observed instead. The
bundled `hooks/hooks.json` registers `hooks/observe_primary_model.py` on
`UserPromptSubmit`; it prints one advisory line when the prompt invokes
`$agent-advisor-codex:orchestration`, and prints nothing otherwise.

Three properties are deliberate, and `tests/test_observe_primary_model.py` pins them:

- **It never blocks.** Every unexpected input path exits 0 with no output, so a host
  that does not supply `model` costs nothing. The hook is not a prerequisite: the gate
  above is unchanged whether or not it is installed.
- **It never claims reasoning effort.** Hook input exposes the model; effort is not
  exposed to hooks. An advisory that implied otherwise would weaken this gate.
- **It never authorizes orchestration**, changes a model, or replaces observed metadata.
  A model line it reports is evidence for the model field only.

## Runtime routing evidence

The public spawn/details record is authoritative for the selected role and any exposed
model/effort. When model or effort is omitted, resolve the helper relative to the
installed skill and inspect the exact native thread ID:

~~~sh
skill_dir=<directory-containing-this-SKILL.md>
runtime_inspector="$skill_dir/../../scripts/inspect-agent-runtime.sh"
sh "$runtime_inspector" <native-subagent-thread-id>
~~~

For a disposable fixture or non-default session root:

~~~sh
sh "$runtime_inspector" --sessions-dir /absolute/path/to/sessions <native-subagent-thread-id>
~~~

The helper searches one exact rollout filename suffix and emits only allowlisted
routing fields. It refuses invalid IDs, zero/multiple matches, missing fields, or
conflicting model/effort/sandbox/permission/working-directory values. It never prints
prompts, messages, environment variables, tokens, configuration, or arbitrary rollout
payloads.

Accepted routing is Luna / max for bounded delegate/full implementation, Terra / high
for higher-risk delegate/full implementation, and Sol / high for audit/full review.
If public and local evidence both exist, they must agree. The local inspector is not a
model-selection fallback.

## Read-only reviewer interpretation

The reviewer TOML requests sandbox_mode = read-only. Capture the observed sandbox
policy type and permission profile type from public metadata or the inspector:

- Observed read-only sandbox: isolation is enforced.
- Broader host policy: continue only when hard isolation is not required, the prompt
  forbids edits, and the parent captures exact before/after repository and artifact
  state. Report the broader policy and profile as residual risk.
- Unobservable isolation, required hard isolation, or any mutation: stop the review and
  do not claim read-only isolation.

A reviewer returns exactly ship, fix-first, or rethink. A fix invalidates the prior
verdict; parent verification and a new fresh review are required.

## Worker packet and parent acceptance

Every Luna or Terra prompt uses the five-part packet in role-contracts.md:

- OBJECTIVE
- FILES AND OWNERSHIP
- INTERFACES
- CONSTRAINTS
- VERIFICATION

It must also request the structured implementation report. The parent owns architecture,
complete diff inspection, verification reruns, correction/escalation decisions, and
acceptance. Worker claims never replace direct inspection.

In solo, the root plans, implements, tests, and self-reviews with no auxiliary. In
delegate, one selected Luna or Terra implementer completes the spec and the root
verifies with no fresh reviewer. In audit, the root implements and verifies, then a
fresh Sol reviewer reviews. In full, one selected implementer completes the spec, the
root verifies, and a fresh Sol reviewer reviews. Auxiliary work substitutes for root
work; it does not duplicate it. A reviewer never fixes its own findings.

## Maintainer verification

From the repository root, run:

~~~sh
sh codex/plugins/agent-advisor-codex/scripts/verify.sh
git diff --check
git status --short
git diff --stat
~~~

The verifier covers the Agent Advisor for Codex 1.0.0 manifest, exact three-role
TOMLs, selective-routing and primary-attestation contracts, installer safety fixtures,
JSON/TOML validity, and shell syntax.
