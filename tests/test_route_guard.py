"""Tests for claude/templates/route-guard.py.

The hook is run the way Claude Code runs it: a JSON payload on stdin, the
decision carried by the exit code. Exit 2 blocks the edit, exit 0 allows it.
"""

import json
import os
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


def assistant_tool(**tool_input):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "name": "Bash", "input": tool_input}]}}


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
                   user("a different task: refactor the dispatch module into pluggable backends"),
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

    # --- declarations carried by tool calls --------------------------------

    def test_declaration_in_a_tool_description_is_allowed(self):
        # Assistant prose is not always persisted to the transcript; tool calls are.
        self.write(user("change the config"),
                   assistant_tool(command="git status", description="SELECTIVE ROUTE: solo (one file)"))
        self.assertEqual(self.run_hook().returncode, 0)

    def test_tool_description_accepts_a_fullwidth_colon(self):
        self.write(user("do it"),
                   assistant_tool(command="ls", description="SELECTIVE ROUTE\uff1adelegate (two repos)"))
        self.assertEqual(self.run_hook().returncode, 0)

    def test_a_command_that_only_searches_for_the_phrase_does_not_count(self):
        self.write(user("do it"),
                   assistant_tool(command="grep -r 'SELECTIVE ROUTE: solo' .",
                          description="look for old declarations"))
        self.assertEqual(self.run_hook().returncode, 2)

    def test_a_tool_description_without_a_mode_does_not_count(self):
        self.write(user("do it"), assistant_tool(command="ls", description="SELECTIVE ROUTE pending"))
        self.assertEqual(self.run_hook().returncode, 2)

    def test_a_tool_declaration_before_the_latest_user_message_does_not_count(self):
        self.write(user("first task"),
                   assistant_tool(command="ls", description="SELECTIVE ROUTE: solo"),
                   user("a different task: migrate the CI pipeline to a matrix build"),
                   assistant_tool(command="ls", description="list files"))
        self.assertEqual(self.run_hook().returncode, 2)

    # --- turn boundaries -------------------------------------------------

    def test_a_background_notification_is_not_a_new_turn(self):
        self.write(user("fix the parser and add tests for every edge case found"),
                   assistant("SELECTIVE ROUTE: solo"),
                   user("<task-notification><status>completed</status></task-notification>"))
        self.assertEqual(self.run_hook().returncode, 0)

    def test_short_follow_up_after_a_declared_turn_is_allowed(self):
        self.write(user("fix the parser"),
                   assistant_tool(command="ls", description="SELECTIVE ROUTE: solo (one module)"),
                   user("continue"),
                   assistant("OK."))
        self.assertEqual(self.run_hook().returncode, 0)

    def test_try_again_after_a_declared_turn_is_allowed(self):
        self.write(user("fix the parser"), assistant("SELECTIVE ROUTE: solo"), user("Try again"))
        self.assertEqual(self.run_hook().returncode, 0)

    def test_a_long_new_instruction_still_needs_its_own_declaration(self):
        self.write(user("first task"),
                   assistant("SELECTIVE ROUTE: solo"),
                   user("now something unrelated: move the test suite from unittest to pytest and wire up CI"))
        self.assertEqual(self.run_hook().returncode, 2)

    def test_a_declaration_older_than_the_carry_window_does_not_count(self):
        self.write(user("task"), assistant("SELECTIVE ROUTE: solo"),
                   user("ok"), assistant("ok"),
                   user("yes"), assistant("ok"),
                   user("sure"), assistant("ok"),
                   user("continue"))
        self.assertEqual(self.run_hook().returncode, 2)

    def test_short_follow_up_without_any_earlier_declaration_is_blocked(self):
        self.write(user("change it"), assistant("OK"), user("continue"))
        self.assertEqual(self.run_hook().returncode, 2)

    # --- scope -----------------------------------------------------------

    def test_auto_memory_writes_are_exempt(self):
        self.write(user("remember this preference and explain the full reasoning behind it"),
                   assistant("no declaration"))
        for path in ("C:/Users/x/.claude/projects/C--Users-x/memory/feedback-x.md",
                     "/home/x/.claude/projects/-home-x-repo/memory/MEMORY.md"):
            self.assertEqual(self.run_hook(path=path).returncode, 0, path)

    def test_other_claude_files_are_not_exempt(self):
        self.write(user("update the dispatch rules and the routing table that points to them"),
                   assistant("no declaration"))
        for path in ("C:/Users/x/.claude/CLAUDE.md",
                     "C:/Users/x/.claude/projects/C--Users-x/notes.md",
                     "C:/repo/memory/store.py"):
            self.assertEqual(self.run_hook(path=path).returncode, 2, path)

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

    # --- Antigravity (--agent antigravity) ----------------------------------

    AG_CONV = "0f0f0f0f-1111-2222-3333-444444444444"
    AG_TASK = "fix the config file, then update its docs and add tests"

    def ag_write(self, *steps):
        # Laid out where the hook looks: <home>/.gemini/antigravity/brain/<conversationId>/...
        logs = Path(self.tmp) / ".gemini" / "antigravity" / "brain" / self.AG_CONV / ".system_generated" / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        self.ag_transcript = logs / "transcript.jsonl"
        self.ag_transcript.write_text(
            "\n".join(json.dumps(s, ensure_ascii=False) for s in steps), encoding="utf-8")

    def ag_run(self, tool="write_to_file", target="C:\\repo\\a.py", via="conversationId",
               argv=("--agent", "antigravity")):
        payload = {"toolCall": {"name": tool, "args": {"TargetFile": target, "CodeContent": "x"}}}
        if via == "conversationId":
            payload["conversationId"] = self.AG_CONV
        else:
            payload["transcriptPath"] = str(self.ag_transcript)
        env = dict(os.environ, USERPROFILE=self.tmp, HOME=self.tmp,
                   ROUTE_GUARD_STATE_DIR=str(Path(self.tmp) / "state"))
        proc = subprocess.run([sys.executable, str(HOOK), *argv], input=json.dumps(payload).encode(),
                              capture_output=True, timeout=60, env=env)
        out = json.loads(proc.stdout.decode("utf-8") or "{}")
        return proc.returncode, out.get("decision")

    @staticmethod
    def ag_user(text):
        return {"type": "USER_INPUT", "source": "USER_EXPLICIT",
                "content": "<USER_REQUEST>\n%s\n</USER_REQUEST>\n<ADDITIONAL_METADATA>x</ADDITIONAL_METADATA>" % text}

    @staticmethod
    def ag_model(text="", tool=None, target="C:\\repo\\a.py", **extra_args):
        step = {"type": "PLANNER_RESPONSE", "source": "MODEL", "content": text}
        if tool:
            # The transcript quotes TargetFile; the live payload does not.
            step["tool_calls"] = [{"name": tool, "args": dict({"TargetFile": '"%s"' % target}, **extra_args)}]
        return step

    def test_antigravity_edit_without_declaration_is_denied(self):
        self.ag_write(self.ag_user(self.AG_TASK), self.ag_model("OK", tool="write_to_file"))
        self.assertEqual(self.ag_run(), (0, "deny"))

    def test_antigravity_declared_in_text_is_allowed_with_ask(self):
        self.ag_write(self.ag_user(self.AG_TASK),
                      self.ag_model("SELECTIVE ROUTE: solo (one file)"),
                      self.ag_model("", tool="write_to_file"))
        self.assertEqual(self.ag_run(), (0, "ask"))

    def test_antigravity_declared_in_tool_summary_is_allowed(self):
        self.ag_write(self.ag_user(self.AG_TASK),
                      self.ag_model("", tool="write_to_file", toolSummary="SELECTIVE ROUTE: solo (one file)"))
        self.assertEqual(self.ag_run(), (0, "ask"))

    def test_antigravity_lagging_transcript_allows(self):
        # The guarded call is not in the transcript yet: cannot judge, so allow.
        self.ag_write(self.ag_user(self.AG_TASK), self.ag_model("OK"))
        self.assertEqual(self.ag_run(), (0, "ask"))

    def test_antigravity_short_follow_up_carries_the_route(self):
        self.ag_write(self.ag_user(self.AG_TASK),
                      self.ag_model("SELECTIVE ROUTE: solo"),
                      self.ag_user("continue"),
                      self.ag_model("", tool="write_to_file"))
        self.assertEqual(self.ag_run(), (0, "ask"))

    def test_antigravity_transcript_path_in_payload_is_used(self):
        self.ag_write(self.ag_user(self.AG_TASK), self.ag_model("OK", tool="write_to_file"))
        self.assertEqual(self.ag_run(via="transcriptPath"), (0, "deny"))

    def test_antigravity_brain_and_unguarded_tools_pass(self):
        self.ag_write(self.ag_user(self.AG_TASK), self.ag_model("OK", tool="write_to_file"))
        self.assertEqual(self.ag_run(target="C:\\Users\\x\\.gemini\\antigravity\\brain\\abc\\task.md"), (0, "ask"))
        self.assertEqual(self.ag_run(tool="run_command"), (0, "ask"))

    def test_antigravity_denies_once_per_turn_then_allows(self):
        # A lagging transcript must not turn a reminder into an endless loop.
        self.ag_write(self.ag_user(self.AG_TASK), self.ag_model("OK", tool="write_to_file"))
        self.assertEqual(self.ag_run(), (0, "deny"))
        self.assertEqual(self.ag_run(), (0, "ask"))

    def test_antigravity_next_turn_gets_its_own_reminder(self):
        self.ag_write(self.ag_user(self.AG_TASK), self.ag_model("OK", tool="write_to_file"))
        self.assertEqual(self.ag_run(), (0, "deny"))
        self.ag_write(self.ag_user(self.AG_TASK),
                      self.ag_model("OK", tool="write_to_file"),
                      self.ag_user("also rewrite the README install section and add the Windows caveats"),
                      self.ag_model("OK", tool="write_to_file"))
        self.assertEqual(self.ag_run(), (0, "deny"))

    def test_antigravity_garbage_payload_still_answers_ask(self):
        proc = subprocess.run([sys.executable, str(HOOK), "--agent", "antigravity"], input=b"{not json",
                              capture_output=True, timeout=60)
        self.assertEqual((proc.returncode, json.loads(proc.stdout)["decision"]), (0, "ask"))

    # --- fail-open: this hook blocks the tools needed to repair it --------

    def test_unexpected_record_shape_allows(self):
        # fail-open covers a record shape the parser did not anticipate, too.
        self.write(user("change the config"),
                   {"type": "assistant", "message": {"role": "assistant", "content": None}})
        proc = self.run_hook()
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_non_string_transcript_path_allows(self):
        raw = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "C:/repo/a.py"},
                          "transcript_path": 123}).encode("utf-8")
        proc = self.run_hook(raw=raw)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_antigravity_unexpected_args_shape_still_answers_ask(self):
        self.ag_write(self.ag_user(self.AG_TASK),
                      {"type": "PLANNER_RESPONSE", "content": "OK",
                       "tool_calls": [{"name": "write_to_file", "args": ["not", "a", "dict"]}]})
        self.assertEqual(self.ag_run(), (0, "ask"))

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
