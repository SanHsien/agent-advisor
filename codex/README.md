# Agent Advisor for Codex

> This Codex edition is maintained in
> [SanHsien/agent-advisor](https://github.com/SanHsien/agent-advisor), derived from
> [DannyMac180/sol-advisor](https://github.com/DannyMac180/sol-advisor). It retains
> the original author attribution and MIT license.

**Sol / High runs the show. It declares a risk-gated route before task tools, keeps
solo as the default, and uses a single auxiliary only when that improves delivery.**

Agent Advisor for Codex is the Codex-native edition of Agent Advisor for capability-routed
software delivery. You
bring the goal and constraints; Sol owns the plan, implementation or delegation,
verification, and acceptance.

Windows-first fork、安裝、四種 route、委派工作包、驗證與維護的繁中步驟，請讀
[**Agent Advisor for Codex 工作流教學（繁中）**](docs/WORKFLOW.zh-TW.md)。

## Quick start

You need a current Codex CLI or ChatGPT desktop app with plugins enabled, GPT-5.6
Sol / High for the primary session, native custom-agent support, and jq. GPT-5.6
Luna / Max or Terra / High access is needed only when the selected route delegates.
Maintainer POSIX verification also requires Python 3.11+ because `verify.sh` uses
the standard-library `tomllib` module, as documented in upstream
[PR #24](https://github.com/DannyMac180/sol-advisor/pull/24) and
[issue #1](https://github.com/DannyMac180/sol-advisor/issues/1).
When primary metadata is unavailable, a bundled first-call inspector verifies the
user-level standing attestation and avoids repeated confirmation; observed conflicts
still stop. See [advanced native operations](plugins/agent-advisor-codex/skills/orchestration/references/operations.md).

To enable that fallback, place this exact line once in the regular user-level
`~/.codex/AGENTS.md` and do not create a user-level `AGENTS.override.md`:

~~~text
AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION: gpt-5.6-sol/high
~~~

~~~sh
codex plugin marketplace add SanHsien/agent-advisor --ref main
codex plugin add agent-advisor-codex@agent-advisor
plugin_dir="$(codex plugin list --json | jq -r '.installed[] | select(.pluginId == "agent-advisor-codex@agent-advisor") | .source.path')" && test -n "$plugin_dir" && test "$plugin_dir" != null && test -d "$plugin_dir" && test -f "$plugin_dir/scripts/install-agents.sh" && sh "$plugin_dir/scripts/install-agents.sh"
~~~

### PowerShell (Windows)

Install the plugin using the normal Codex command, then run the companion installer
from the installed plugin directory. The installer does not edit Codex configuration.

~~~powershell
$pluginDir = (codex plugin list --json | ConvertFrom-Json).installed | Where-Object { $_.pluginId -eq 'agent-advisor-codex@agent-advisor' } | Select-Object -First 1 -ExpandProperty source | Select-Object -ExpandProperty path
if (-not $pluginDir -or -not (Test-Path -LiteralPath (Join-Path $pluginDir 'scripts/install-agents.ps1') -PathType Leaf)) { throw 'Agent Advisor for Codex installer was not found.' }
& (Join-Path $pluginDir 'scripts/install-agents.ps1')
~~~

The companion installer verifies all three exact role files after installation. It is
fail-closed: modified, unsafe, nonregular, symlinked, unknown, or differing files
are left untouched. It does not edit Codex configuration. Start a fresh Codex task
after installation so native roles are discovered.

Use this one prompt in the new task:

~~~text
Use $agent-advisor-codex:orchestration to build this feature and verify it. Declare the selective route before task tools.
~~~

## What you do

Give Sol the outcome, constraints, and any important repository context. You do not
need to select or manage a lane; Sol records the route and owns verification and
acceptance.

## Routes

| Mode | Use it when | Delivery |
|---|---|---|
| `solo` | Default; risk is contained. | Root plans, implements, tests, and self-reviews. |
| `delegate` | A complete spec is better executed by one implementer. | Luna / Max for bounded work, or Terra / High for judgment-heavy or high-risk work; root verifies. |
| `audit` | Independent final scrutiny matters more than delegation. | Root implements; a fresh read-only Sol / High reviews. |
| `full` | Explicit broad or high-risk exception. | One selected implementer, root verification, and a fresh Sol / High review. |

Solo is the default. One auxiliary is the default maximum; `full` is the explicit
exception. Sol emits a `SELECTIVE ROUTE` declaration with the mode and concise risk
rationale before the first task tool call. It can escalate only when newly observed
risk justifies it and never silently downgrades.

## What happens automatically

Sol / High keeps architecture, decomposition, route selection, parent verification,
escalation decisions, and acceptance in the primary task. Auxiliary work substitutes
for root work; it does not duplicate it. The root inspects the complete diff and
reruns the requested checks. When the selected route includes a review, a fresh Sol /
High reviewer returns ship, fix-first, or rethink; any fix requires a new review.

## Updating

Update the marketplace plugin, reinstall the companion roles, and start a new task:

~~~sh
codex plugin marketplace upgrade agent-advisor
codex plugin add agent-advisor-codex@agent-advisor
plugin_dir="$(codex plugin list --json | jq -r '.installed[] | select(.pluginId == "agent-advisor-codex@agent-advisor") | .source.path')" && test -n "$plugin_dir" && test "$plugin_dir" != null && test -d "$plugin_dir" && test -f "$plugin_dir/scripts/install-agents.sh" && sh "$plugin_dir/scripts/install-agents.sh"
~~~

For exact spawn, runtime-evidence, sandbox, installer, and maintainer verification
details, read [advanced native operations](plugins/agent-advisor-codex/skills/orchestration/references/operations.md).
For local development, install this checkout as a marketplace:

~~~sh
cd /absolute/path/to/agent-advisor
codex plugin marketplace add /absolute/path/to/agent-advisor
codex plugin add agent-advisor-codex@agent-advisor
~~~

For Windows-first development, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md). Fork
maintenance and upstream review policy are in [the shared fork guide](../docs/FORK.md)
and [upstream ledger](../docs/UPSTREAM.md).
