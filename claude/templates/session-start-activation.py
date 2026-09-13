#!/usr/bin/env python3
"""SessionStart hook: inject the agent-advisor selective-routing directive.

OPTIONAL. ``~/.claude/CLAUDE.md`` is already loaded into every session, so the
CLAUDE.md snippet on its own activates routing. This hook adds a second,
independent channel (``hookSpecificOutput.additionalContext``) that keeps the
directive in model context even after a long conversation is compacted.

Install: copy to ``~/.claude/hooks/session-start-activation.py`` and wire it up
with the ``hooks.SessionStart`` block in ``claude/templates/settings-example.json``.

Windows note: call it as ``python "<absolute path>"``. A hook command starting
with a bare ``bash`` resolves to WSL, where the home directory differs and the
script does not exist, so the hook silently never runs.

Merging with an existing SessionStart hook: emit one JSON object per hook
command. Claude Code concatenates the ``additionalContext`` of every hook that
returns one, so an existing hook does not need to be rewritten -- just register
this one alongside it.
"""

import json
import sys

DIRECTIVE = (
    "[agent-advisor persistent routing] The plugin agent-advisor-claude is installed. "
    "Before any non-trivial task (editing files, multi-file search, implementation, "
    "refactoring, debugging), load Skill(\"agent-advisor-claude:orchestration\") and "
    "declare a SELECTIVE ROUTE before starting work: one of solo / delegate / audit / "
    "exceptional full, with a one-line reason. Single questions, status lookups, and "
    "chat need no declaration. If the plugin is not loaded, skip this step without "
    "raising an error."
)


def main() -> int:
    # Claude Code passes hook input on stdin; this hook does not need it, but it
    # must be drained so the writing end never blocks.
    try:
        sys.stdin.read()
    except Exception:  # noqa: BLE001 - a closed stdin must not fail the session
        pass

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": DIRECTIVE,
            }
        },
        sys.stdout,
        ensure_ascii=False,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
