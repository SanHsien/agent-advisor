"""Tests for claude/templates/route-guard.py.

The hook is run the way Claude Code runs it: a JSON payload on stdin, the
decision carried by the exit code. Exit 2 blocks the edit, exit 0 allows it.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HOOK = REPO / "claude" / "templates" / "route-guard.py"


def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def tool_result(text):
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "content": text}]}}


def assistant(text):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": text}]}}


class RouteGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.transcript = Path(self.tmp) / "transcript.jsonl"

    def write(self, *records):
        self.transcript.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records),
            encoding="utf-8",
        )

    def run_hook(self, tool="Edit", path="C:/repo/src/app.py", transcript=True, raw=None):
        if raw is None:
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": tool,
                "tool_input": {"file_path": path},
            }
            if transcript:
                payload["transcript_path"] = str(self.transcript)
            raw = json.dumps(payload).encode("utf-8")
        return subprocess.run(
            [sys.executable, str(HOOK)], input=raw, capture_output=True, timeout=60
        )

    # --- enforcement -----------------------------------------------------

    def test_edit_without_a_declaration_is_blocked(self):
        self.write(user("change the config"), assistant("Sure, editing now."))
        proc = self.run_hook()
        self.assertEqual(proc.returncode, 2)
        self.assertIn("SELECTIVE ROUTE", proc.stderr.decode("utf-8", "replace"))

    def test_edit_after_a_declaration_is_allowed(self):
        self.write(user("change the config"),
                   assistant("SELECTIVE ROUTE: solo (one file)"))
        self.assertEqual(self.run_hook().returncode, 0)

    def test_declaration_is_case_insensitive(self):
        self.write(user("do it"), assistant("selective route: solo"))
        self.assertEqual(self.run_hook().returncode, 0)

    def test_a_declaration_before_the_latest_user_message_does_not_count(self):
        # Otherwise one declaration at session start licenses every later edit.
        self.write(user("first task"),
                   assistant("SELECTIVE ROUTE: solo"),
                   user("a different task"),
                   assistant("Starting."))
        self.assertEqual(self.run_hook().returncode, 2)

    def test_tool_results_do_not_reset_the_declaration(self):
        # Tool results are also type "user"; counting them as new instructions
        # would demand a re-declaration after every single tool call.
        self.write(user("do it"),
                   assistant("SELECTIVE ROUTE: solo"),
                   tool_result("command output"),
                   assistant("Continuing."))
        self.assertEqual(self.run_hook().returncode, 0)

    # --- scope -----------------------------------------------------------

    def test_every_guarded_tool_is_covered(self):
        self.write(user("do it"), assistant("no declaration"))
        for tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            self.assertEqual(self.run_hook(tool=tool).returncode, 2, tool)

    def test_other_tools_pass_through(self):
        self.write(user("do it"), assistant("no declaration"))
        for tool in ("Bash", "Read", "Grep", "Glob"):
            self.assertEqual(self.run_hook(tool=tool).returncode, 0, tool)

    def test_scratch_paths_are_exempt(self):
        self.write(user("do it"), assistant("no declaration"))
        proc = self.run_hook(path="C:/Users/x/AppData/Local/Temp/scratchpad/probe.py")
        self.assertEqual(proc.returncode, 0)

    # --- fail-open: this hook blocks the tools needed to repair it --------

    def test_missing_transcript_path_allows(self):
        self.assertEqual(self.run_hook(transcript=False).returncode, 0)

    def test_unreadable_transcript_allows(self):
        self.assertEqual(self.run_hook().returncode, 0)  # never written

    def test_garbage_transcript_allows(self):
        self.transcript.write_text("not json\n{broken", encoding="utf-8")
        self.assertEqual(self.run_hook().returncode, 0)

    def test_transcript_without_any_user_message_allows(self):
        self.write(assistant("assistant only"))
        self.assertEqual(self.run_hook().returncode, 0)

    def test_malformed_payload_allows(self):
        self.assertEqual(self.run_hook(raw=b"{not json").returncode, 0)

    def test_empty_payload_allows(self):
        self.assertEqual(self.run_hook(raw=b"").returncode, 0)


if __name__ == "__main__":
    unittest.main()
