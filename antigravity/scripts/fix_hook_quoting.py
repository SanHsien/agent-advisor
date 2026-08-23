#!/usr/bin/env python3
"""Repair quoted script paths in an Antigravity ``hooks.json``.

Antigravity splits a hook command into argv itself instead of handing it to a
shell, so a quoted script path keeps its quote characters inside the filename and
the interpreter fails with ``[Errno 22] Invalid argument``. Because ``PreToolUse``
hooks run before the tool does, every guarded tool call then fails -- including
the ones an agent would need to repair the file. That is why this ships as a
standalone script a human can run from a plain terminal.

Claude Code runs hook commands through a shell, where the quoted form is correct.
Do not run this against ``~/.claude/settings.json``.

Default is a dry run. Pass ``--apply`` to write, which first copies the file to
``<name>.bak-<timestamp>`` and re-parses the result before returning success.

    python antigravity/scripts/fix_hook_quoting.py
    python antigravity/scripts/fix_hook_quoting.py --apply
    python antigravity/scripts/fix_hook_quoting.py --path /custom/hooks.json --apply
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import re
import shutil
import sys

# "python \"C:\\path\\x.py\"" -> interpreter, then a fully quoted remainder.
QUOTED = re.compile(r'^(python3?|py)\s+"(.+)"$')

DEFAULT_PATH = pathlib.Path.home() / ".gemini" / "config" / "hooks.json"


def rewrite(node: object, found: list[tuple[str, str]]) -> None:
    """Walk the config and unquote every hook command path in place."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "command" and isinstance(value, str):
                match = QUOTED.match(value)
                if match:
                    fixed = f"{match.group(1)} {match.group(2)}"
                    found.append((value, fixed))
                    node[key] = fixed
            else:
                rewrite(value, found)
    elif isinstance(node, list):
        for item in node:
            rewrite(item, found)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--path", type=pathlib.Path, default=DEFAULT_PATH)
    parser.add_argument("--apply", action="store_true", help="write the fix (default: dry run)")
    args = parser.parse_args(argv)

    path: pathlib.Path = args.path
    if not path.is_file():
        print(f"not found: {path}", file=sys.stderr)
        return 2

    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"{path} is not valid JSON, refusing to touch it: {exc}", file=sys.stderr)
        return 2

    found: list[tuple[str, str]] = []
    rewrite(config, found)

    if not found:
        print(f"{path}: nothing to fix, no quoted hook command paths found.")
        return 0

    for before, after in found:
        print(f"- {before}\n+ {after}")

    if not args.apply:
        print(f"\n{len(found)} command(s) would change. Re-run with --apply to write.")
        return 0

    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f"{path.name}.bak-{stamp}")
    shutil.copy2(path, backup)
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # A repair that leaves the file unparseable is worse than the bug it fixed.
    json.loads(path.read_text(encoding="utf-8"))
    print(f"\n{len(found)} command(s) fixed. Backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
