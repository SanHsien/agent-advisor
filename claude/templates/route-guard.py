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

Antigravity: the same file also guards Antigravity when its ``hooks.json``
registers it with ``--agent antigravity`` (see
``antigravity/templates/hooks-example.json``). Antigravity's PreToolUse payload
carries only ``toolCall`` and ``conversationId``; the transcript lives at
``~/.gemini/antigravity/brain/<id>/.system_generated/logs/transcript.jsonl`` and
is written on Antigravity's own schedule. So the hook judges only once the
guarded call is already visible in the current turn, and it denies at most once
per conversation turn (state in the temp directory), so a lagging transcript
cannot turn the reminder into an endless loop. Every allow answers
``{"decision": "ask"}``, because Antigravity reads an answer without a decision
as a deny.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

GUARDED_TOOLS = {"edit", "write", "multiedit", "notebookedit"}
# Antigravity file-writing tools, measured from its own transcripts (desktop and
# CLI name them differently).
ANTIGRAVITY_GUARDED_TOOLS = {
    "write_to_file", "replace_file_content", "multi_replace_file_content", "edit_file", "write_file",
}
# Antigravity keeps one transcript per conversation; its PreToolUse payload
# carries only conversationId (Stop also carries transcriptPath).
ANTIGRAVITY_BRAIN = Path.home() / ".gemini" / "antigravity" / "brain"
ANTIGRAVITY_DECLARATION_ARGS = ("toolSummary", "toolAction", "Description")
USER_REQUEST = re.compile(r"<USER_REQUEST>(.*?)</USER_REQUEST>", re.DOTALL)
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
# A background-task notification arrives as a type "user" record, but the
# operator did not say anything, so it must not close the declaration window.
# Counting one as a turn boundary denies edits for a task that was declared,
# and a spawned subagent (which declares in its own transcript) can never
# satisfy the gate once a notification lands in the parent's.
NOTIFICATION = re.compile(
    r"<task-notification>|SYSTEM NOTIFICATION - NOT USER INPUT"
    r"|<agent-message from=|\[Subagent hand-back\]",
    re.IGNORECASE,
)
# Scratch and temp files are working material, not deliverables.
EXEMPT_PATH_PARTS = ("scratchpad", "\\temp\\", "/temp/", "\\tmp\\", "/tmp/")
# Auto-memory upkeep is housekeeping that is never delegated, so a route adds
# nothing. Measured over 30 days: 64 of 291 denials were memory writes.
# Antigravity's brain/ (its own plans and task lists) and knowledge/ (its
# memory) are the same kind of material.
EXEMPT_PATH_PATTERNS = (
    re.compile(r"[\\/]\.claude[\\/]projects[\\/][^\\/]+[\\/]memory[\\/]", re.IGNORECASE),
    re.compile(r"[\\/]\.gemini[\\/]antigravity[\\/](?:brain|knowledge)[\\/]", re.IGNORECASE),
)
# A short message ("continue", "Try again", "yes") right after a declared turn
# continues that task. Measured over 30 days: 69 of 126 denied turns had a
# route declared within the previous three turns. Both limits keep a fresh,
# real task from riding on an old route.
CARRY_TURNS = 3
SHORT_FOLLOW_UP_CHARS = 40
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


def tool_args(payload: dict) -> dict:
    src = payload.get("tool_input") or payload.get("toolInput")
    if not isinstance(src, dict) or not src:
        call = payload.get("toolCall") or {}
        src = call.get("args") or call.get("arguments") or call.get("input") or {}
    return src if isinstance(src, dict) else {}


def target_path(payload: dict) -> str:
    src = tool_args(payload)
    for key in ("file_path", "filePath", "path", "notebook_path", "TargetFile", "Path", "AbsolutePath"):
        value = src.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def content_text(content) -> str:
    """Flatten a message's content to searchable text; never raise."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts)
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

    boundaries = []
    for i, obj in enumerate(records):
        if obj.get("type") != "user":
            continue
        content = (obj.get("message") or {}).get("content")
        if isinstance(content, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in content
        ):
            continue
        if NOTIFICATION.search(content_text(content)):
            continue
        boundaries.append(i)
    if not boundaries:
        return True

    last_user = boundaries[-1]
    if declared_in(records[last_user + 1:]):
        return True

    # Continuation: a short follow-up right after a declared turn.
    message = content_text((records[last_user].get("message") or {}).get("content")).strip()
    if len(message) > SHORT_FOLLOW_UP_CHARS:
        return False
    recent = boundaries[-1 - CARRY_TURNS:]
    for start, end in zip(recent, recent[1:]):
        if declared_in(records[start + 1:end]):
            return True
    return False


def declared_in(records: list) -> bool:
    """True when an assistant record in this slice declared a route."""
    for obj in records:
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


ANTIGRAVITY_REASON = """Declare a SELECTIVE ROUTE before editing files (agent-advisor selective-routing rule).

This turn has no route declaration yet. Write one line in your reply first, for example:

  SELECTIVE ROUTE: solo (one sentence of reasoning)

Pick one of: solo / delegate / audit / exceptional full. Then retry this edit."""


def is_antigravity(payload: dict) -> bool:
    return isinstance(payload.get("toolCall"), dict) or "conversationId" in payload


def bare(value) -> str:
    """Normalise a path for comparison; transcripts quote and double-escape it."""
    return str(value or "").strip().strip('"').replace("\\\\", "\\").replace("/", "\\").lower()


def antigravity_transcript(payload: dict) -> str:
    path = payload.get("transcriptPath")
    if isinstance(path, str) and path:
        return path
    conv = payload.get("conversationId")
    if isinstance(conv, str) and re.fullmatch(r"[0-9a-fA-F-]{8,64}", conv):
        return str(ANTIGRAVITY_BRAIN / conv / ".system_generated" / "logs" / "transcript.jsonl")
    return ""


def antigravity_declared(path: str, name: str, target: str) -> bool:
    """Antigravity flavour of declared_since_last_user_message.

    Antigravity writes the transcript on its own schedule, so the hook only
    judges once the very call it is guarding is visible in the current turn.
    If it is not there yet, the transcript is lagging and the answer is
    unknown -- allow, as everywhere else in this hook.
    """
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return True
    steps = []
    for line in lines[-4000:]:
        line = line.strip()
        if line.startswith("{"):
            try:
                steps.append(json.loads(line))
            except ValueError:
                continue
    boundaries = [i for i, s in enumerate(steps) if s.get("type") == "USER_INPUT"]
    if not boundaries:
        return True
    last_user = boundaries[-1]

    current = steps[last_user + 1:]
    if not any(
        isinstance(call, dict) and str(call.get("name", "")).lower() == name
        and any(bare(v) == target for v in (call.get("args") or {}).values())
        for s in current for call in (s.get("tool_calls") or [])
    ):
        return True  # transcript has not caught up with this call yet

    if antigravity_declared_in(current):
        return True
    request = steps[last_user].get("content") or ""
    match = USER_REQUEST.search(request)
    message = (match.group(1) if match else request).strip()
    if len(message) > SHORT_FOLLOW_UP_CHARS:
        return False
    recent = boundaries[-1 - CARRY_TURNS:]
    return any(antigravity_declared_in(steps[a + 1:b]) for a, b in zip(recent, recent[1:]))


def antigravity_declared_in(steps: list) -> bool:
    for s in steps:
        if s.get("type") != "PLANNER_RESPONSE":
            continue
        text = s.get("content")
        if isinstance(text, str) and DECLARATION.search(text):
            return True
        for call in s.get("tool_calls") or []:
            args = call.get("args") if isinstance(call, dict) else None
            if isinstance(args, dict) and any(
                isinstance(args.get(k), str) and TOOL_DECLARATION.search(args[k])
                for k in ANTIGRAVITY_DECLARATION_ARGS
            ):
                return True
    return False


def first_reminder_this_turn(transcript: str) -> bool:
    """Deny at most once per Antigravity turn.

    When the transcript lags a step behind, a retry that follows a fresh
    declaration still looks undeclared, and denying it would loop forever with
    no way out. One reminder per turn keeps the nudge and rules out the loop.
    Returns True when this is the turn's first denial (and records it).
    """
    try:
        lines = Path(transcript).read_text(encoding="utf-8", errors="replace").splitlines()
        turn = sum(1 for line in lines if '"USER_INPUT"' in line)
        state_dir = Path(os.environ.get("ROUTE_GUARD_STATE_DIR") or (Path(tempfile.gettempdir()) / "route_guard"))
        state_dir.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(str(Path(transcript).resolve()).lower().encode("utf-8")).hexdigest()[:24]
        state = state_dir / (key + ".turn")
        if state.exists() and state.read_text(encoding="utf-8").strip() == str(turn):
            return False
        state.write_text(str(turn), encoding="utf-8")
        return True
    except OSError:
        return False  # cannot remember the denial, so do not risk a loop


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


def judge(payload: dict) -> bool:
    """True = allow."""
    antigravity = is_antigravity(payload)
    name = tool_name(payload)
    if name not in (ANTIGRAVITY_GUARDED_TOOLS if antigravity else GUARDED_TOOLS):
        return True

    path = target_path(payload).strip().strip('"').replace("/", os.sep).lower()
    if any(part.replace("/", os.sep).lower() in path for part in EXEMPT_PATH_PARTS):
        return True
    if any(p.search(path) for p in EXEMPT_PATH_PATTERNS):
        return True

    if antigravity:
        transcript = antigravity_transcript(payload)
        if not transcript or antigravity_declared(transcript, name, bare(target_path(payload))):
            return True
        return not first_reminder_this_turn(transcript)
    transcript = payload.get("transcript_path")
    if not transcript:
        return True  # nothing to judge from
    return declared_since_last_user_message(transcript)


def main() -> int:
    # Antigravity reads a PreToolUse answer without a decision as a deny, so its
    # registration passes --agent antigravity and every allow says "ask".
    antigravity_cli = "antigravity" in sys.argv[1:]
    try:
        payload = read_payload()
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        payload = None
    if isinstance(payload, dict) and not judge(payload):
        if antigravity_cli or is_antigravity(payload):
            sys.stdout.write(json.dumps({"decision": "deny", "reason": ANTIGRAVITY_REASON}, ensure_ascii=False))
            return 0
        return deny(payload, REASON)
    if antigravity_cli or (isinstance(payload, dict) and is_antigravity(payload)):
        sys.stdout.write(json.dumps({"decision": "ask"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
