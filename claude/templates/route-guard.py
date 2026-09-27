#!/usr/bin/env python3
"""PreToolUse hook: refuse to edit files until a route has been declared.

The CLAUDE.md snippet and the SessionStart hook both put the SELECTIVE ROUTE
directive in front of the model. Neither one enforces it -- following the
directive is still the model's own choice, and a directive that is only ever
read is the first thing to go when a turn gets long.

This hook closes that gap. It runs before Edit / Write / MultiEdit /
NotebookEdit, looks back at what the assistant has said since the most recent
user message, and blocks the edit when no route was declared. The refusal text
tells the model exactly what to write, so recovering costs one sentence.

Install: copy to ``~/.claude/hooks/route-guard.py`` and register it with the
``hooks.PreToolUse`` block in ``claude/templates/settings-example.json``.

Scope is per turn, not per session, and that is the whole point: a single
declaration at session start would otherwise license every edit for the rest of
the day. Tool results also arrive as ``type: "user"`` records and are skipped,
otherwise every tool call would demand a fresh declaration.

Fail-open is deliberate and wider here than in a normal guard. This hook blocks
the very tools needed to repair it, so an unreadable transcript, an unfamiliar
payload shape, or a missing path all allow the edit. It exists to catch "forgot
to declare", not to prove that a declaration happened.

The declaration is also read from tool-call descriptions. Claude Code does not
always write the assistant's prose to the transcript (one measured session:
818 assistant records, 45 with a text block), but it always writes tool-call
arguments. Reading prose alone turns a real declaration into a false block.

Windows note: register it as ``python "<absolute path>"``. A hook command
starting with a bare ``bash`` resolves to WSL, where the home directory differs
and the script does not exist, so the hook silently never runs.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

GUARDED_TOOLS = {"edit", "write", "multiedit", "notebookedit"}
DECLARATION = re.compile(r"SELECTIVE\s+ROUTE", re.IGNORECASE)
# A tool call's own arguments are always written to the transcript; the
# assistant's prose is not (one measured session: 818 assistant records, only
# 45 with a text block, although nearly every message had visible text). A
# declaration may therefore also ride in a tool call's description. The full
# form is required there, so a command that merely searches for the phrase
# does not count.
TOOL_DECLARATION = re.compile(
    r"SELECTIVE\s+ROUTE\s*[:\uff1a]\s*(?:solo|delegate|audit|full)\b", re.IGNORECASE
)
TOOL_DECLARATION_FIELDS = ("description",)
# Scratch and temp files are working material, not deliverables.
EXEMPT_PATH_PARTS = ("scratchpad", "\\temp\\", "/temp/", "\\tmp\\", "/tmp/")
MAX_TRANSCRIPT_BYTES = 512_000

REASON = """Declare a SELECTIVE ROUTE before editing files.

This turn has no route declaration yet. Write one line first, for example:

  SELECTIVE ROUTE: solo (one sentence of reasoning)

Pick one of: solo / delegate / audit / exceptional full.
Single questions, status checks, and chat never reach this hook.
Once declared, simply retry the edit.

Already declared and still blocked? Assistant prose is not always written to
the transcript. Repeat the declaration at the start of the next tool call's
description (a read-only Bash is enough), e.g. "SELECTIVE ROUTE: solo (reason)",
then retry the edit."""


def read_payload() -> dict:
    raw = sys.stdin.buffer.read().decode("utf-8", "replace")
    return json.loads(raw) if raw.strip() else {}


def tool_name(payload: dict) -> str:
    name = payload.get("tool_name") or payload.get("toolName") or ""
    if not name:
        call = payload.get("toolCall") or {}
        name = call.get("name") or call.get("tool") or ""
    return str(name).strip().lower()


def target_path(payload: dict) -> str:
    src = payload.get("tool_input") or payload.get("toolInput") or {}
    if not isinstance(src, dict):
        call = payload.get("toolCall") or {}
        src = call.get("arguments") or call.get("input") or {}
    if not isinstance(src, dict):
        return ""
    for key in ("file_path", "filePath", "path", "notebook_path"):
        value = src.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def declared_since_last_user_message(path: str) -> bool:
    """True when a route was declared after the latest user instruction.

    Returns True whenever the answer cannot be established: an unreadable or
    unrecognised transcript must never make editing impossible.
    """
    try:
        data = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return True
    if len(data) > MAX_TRANSCRIPT_BYTES:
        data = data[-MAX_TRANSCRIPT_BYTES:]

    records = []
    for line in data.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    if not records:
        return True

    last_user = -1
    for i, obj in enumerate(records):
        if obj.get("type") != "user":
            continue
        content = (obj.get("message") or {}).get("content")
        if isinstance(content, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in content
        ):
            continue
        last_user = i
    if last_user < 0:
        return True

    for obj in records[last_user + 1:]:
        if obj.get("type") != "assistant":
            continue
        for blk in (obj.get("message") or {}).get("content", []):
            if not isinstance(blk, dict):
                continue
            if blk.get("type") == "tool_use":
                args = blk.get("input")
                if isinstance(args, dict) and any(
                    isinstance(args.get(field), str)
                    and TOOL_DECLARATION.search(args[field])
                    for field in TOOL_DECLARATION_FIELDS
                ):
                    return True
                continue
            text = blk.get("text") or ""
            if isinstance(text, str) and DECLARATION.search(text):
                return True
    return False


def deny(payload: dict, msg: str) -> int:
    if payload.get("cursor_version"):
        sys.stdout.write(json.dumps(
            {"permission": "deny", "agent_message": msg, "user_message": msg},
            ensure_ascii=False,
        ))
        return 2
    if "toolCall" in payload:
        sys.stdout.write(json.dumps({"decision": "deny", "reason": msg}, ensure_ascii=False))
        return 0
    sys.stderr.write(msg)
    return 2


def main() -> int:
    try:
        payload = read_payload()
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return 0

    if tool_name(payload) not in GUARDED_TOOLS:
        return 0

    path = target_path(payload).replace("/", os.sep).lower()
    if any(part.replace("/", os.sep).lower() in path for part in EXEMPT_PATH_PARTS):
        return 0

    transcript = payload.get("transcript_path")
    if not transcript:
        return 0
    if declared_since_last_user_message(transcript):
        return 0
    return deny(payload, REASON)


if __name__ == "__main__":
    sys.exit(main())
