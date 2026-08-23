# Templates

Copy-paste material for turning an installed `agent-advisor-claude` plugin into a
routing rule that applies to every session. Nothing here runs from the repository:
each file is meant to be copied into the user's `~/.claude/` directory.

| File | Copy to | Purpose |
| --- | --- | --- |
| [`claude-md-snippet.md`](claude-md-snippet.md) | paste into `~/.claude/CLAUDE.md` | **Primary method.** Makes the SELECTIVE ROUTE declaration the default for every session. |
| [`settings-example.json`](settings-example.json) | merge into `~/.claude/settings.json` | Opus model + `effortLevel`, plus the optional hook wiring. |
| [`session-start-activation.py`](session-start-activation.py) | `~/.claude/hooks/` | Optional fallback that injects the directive through an independent channel. |

Start with the CLAUDE.md snippet. It is loaded into every session on its own, so the
hook is only worth adding if you also want the directive to survive context compaction.

Full instructions, prerequisites, and the three traps that make a correct setup look
broken: [`../docs/ACTIVATION.zh-TW.md`](../docs/ACTIVATION.zh-TW.md).
