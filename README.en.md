English | [中文版](README.md)

# Agent Advisor

> Maintained at [SanHsien/agent-advisor](https://github.com/SanHsien/agent-advisor).
> The Codex edition is derived from
> [DannyMac180/sol-advisor](https://github.com/DannyMac180/sol-advisor) and retains
> the original attribution and MIT license.

Agent Advisor packages the same risk-gated delivery workflow for two native agent
runtimes. Pick the edition that matches the tool running your development session:

| Edition | Native roles | Plugin | Guide |
| --- | --- | --- | --- |
| Codex | Sol primary; optional Luna, Terra, and Sol reviewer lanes | `agent-advisor-codex` | [Agent Advisor for Codex](codex/README.md) |
| Claude Code | Opus primary; optional Haiku, Sonnet, and Opus reviewer lanes | `agent-advisor-claude` | [Agent Advisor for Claude Code](claude/README.md) |
| Cursor | Explicit high-capability primary; optional Composer, Sonnet, and Opus reviewer lanes | `agent-advisor-cursor` | [Agent Advisor for Cursor](cursor/README.md) |
| Antigravity | Pro-tier primary; optional flash, pro, and pro reviewer lanes | `agent-advisor-antigravity` | [Agent Advisor for Antigravity](antigravity/README.md) |

Every edition preserves four routes: `solo`, `delegate`, `audit`, and exceptional
`full`. The primary agent owns architecture, route selection, verification, and final
acceptance. Delegation is selective, never ceremonial.

Where each runtime provides it, activation ships inside the plugin: the Cursor and
Antigravity editions bundle an always-on rule, so installing the plugin is enough to make
route declaration standing behaviour. The Claude Code edition needs a user-level
`CLAUDE.md` edit instead — see its
[persistent activation](claude/README.md#persistent-activation) section.

## Install

### Codex

~~~sh
codex plugin marketplace add SanHsien/agent-advisor --ref main
codex plugin add agent-advisor-codex@agent-advisor
~~~

The Codex plugin also ships native role profiles that require its companion installer.
Follow the complete [Codex quick start](codex/README.md#quick-start).

### Claude Code

Inside Claude Code, run:

~~~text
/plugin marketplace add SanHsien/agent-advisor
/plugin install agent-advisor-claude@agent-advisor
~~~

Start a new session with Opus, then ask:

~~~text
Use /agent-advisor-claude:orchestration to declare a SELECTIVE ROUTE before task tools, then build and verify this feature.
~~~

See the [Claude Code quick start](claude/README.md#quick-start) for validation and
runtime caveats. To make route declaration the standing behaviour of every session
instead of a per-prompt request, see
[persistent activation](claude/README.md#persistent-activation).

### Cursor

Install from the **Customize** panel in the sidebar, or point Cursor's local plugin
folder at this repository:

~~~sh
ln -s "$PWD/cursor/plugins/agent-advisor-cursor" ~/.cursor/plugins/local/agent-advisor-cursor
~~~

Select a high-capability reasoning model — not `auto` — and start work. The bundled
always-apply rule requests the route declaration on its own. See the
[Cursor quick start](cursor/README.md#quick-start).

### Antigravity

~~~sh
agy plugin install ./antigravity/plugins/agent-advisor-antigravity
agy plugin list
~~~

Start a session on a pro-tier model at high effort. The bundled rule requests the route
declaration on its own. See the
[Antigravity quick start](antigravity/README.md#quick-start).

**Read this before wiring a hook**: an Antigravity hook command must not quote its script
path, and a quoted one takes the whole session down. Cause and repair:
[the hook quoting trap](antigravity/README.md#the-hook-quoting-trap).

## Repository layout

~~~text
codex/        Codex marketplace source, plugin, native role profiles, and verifier
claude/       Claude Code marketplace source, plugin, Markdown subagents, activation
              templates, and verifier
cursor/       Cursor plugin, subagents, always-apply rule, and verifier
antigravity/  Antigravity plugin, subagents, always-active rule, fallback templates,
              and verifier
docs/         Shared fork and upstream-maintenance records
tests/        Repository-level unit tests
tools/        Cross-platform repository gate
~~~

The root `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json` are
small discovery catalogs required by the Codex and Claude Code CLIs. All runtime
implementation files live under their platform subdirectory. Cursor and Antigravity are
installed from their plugin directory rather than from a root catalog, so they add no
files at the repository root.

## Development

Run the Windows-first repository gate:

~~~powershell
pwsh -NoProfile -File tools/dev_check.ps1
~~~

Run the unit tests on their own:

~~~sh
python -m unittest discover -s tests -p "test_*.py"
~~~

Platform-specific documentation lives in [codex/docs](codex/docs),
[claude/docs](claude/docs), [cursor/docs](cursor/docs), and
[antigravity/docs](antigravity/docs). Fork maintenance and attribution are documented in
[docs/FORK.md](docs/FORK.md) and [docs/UPSTREAM.md](docs/UPSTREAM.md).

## Related tools

These four repositories each govern a different layer of AI coding. Use one on its own, or stack them:

| Layer | Repo | What it does |
| --- | --- | --- |
| Dispatch decision | **Agent Advisor (you are here)** | Risk-gated routing -- `solo`, `delegate`, `audit`, `full`: whether to delegate at all, and to whom |
| Action interception | [harness-guard](https://github.com/SanHsien/harness-guard) | Agent runtime hooks that actually block dangerous commands, unevidenced claims, and commits over red tests |
| Output quality | [ai-quality-gates](https://github.com/SanHsien/ai-quality-gates) | Executable specs and quantified thresholds: coverage, mutation, cyclomatic complexity, dependency structure, bounded loop policy |
| Delivery lifecycle | [paulsha-cortex](https://github.com/SanHsien/paulsha-cortex) | Multi-agent lifecycle: Candidate -> Verify -> Independent Review -> Delivery -> CompletionRecord |

Adjacent but a different layer: [opencodex](https://github.com/SanHsien/opencodex) is a provider proxy that decides which LLMs these agents can run on. It does not constrain agent behaviour.
