"""Contract tests for antigravity/scripts/fix_hook_quoting.py.

The script repairs a config that, when broken, blocks every guarded tool call in
an Antigravity session. A repair tool for that situation has to be trustworthy on
its own: it must not write during a dry run, must never leave the file
unparseable, and must keep a backup. These tests pin exactly that.
"""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "antigravity" / "scripts" / "fix_hook_quoting.py"

_spec = importlib.util.spec_from_file_location("fix_hook_quoting", SCRIPT)
fixer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fixer)


BROKEN = {
    "danger-zone-guard": {
        "enabled": True,
        "PreToolUse": [
            {
                "matcher": "run_command",
                "hooks": [
                    {
                        "type": "command",
                        "command": 'python "C:\\Users\\me\\.claude\\hooks\\danger_zone_guard.py"',
                        "timeout": 10,
                    }
                ],
            }
        ],
    },
    "lint-gate": {
        "enabled": True,
        "Stop": [
            {
                "type": "command",
                "command": 'python3 "/home/me/hooks/lint_gate.py"',
                "timeout": 60,
            }
        ],
    },
}


def run(*argv):
    """Run the script's entry point, returning (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = fixer.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class FixHookQuotingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.path = self.tmp / "hooks.json"
        self.write(BROKEN)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, data):
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def commands(self, path=None):
        found = []

        def walk(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "command":
                        found.append(value)
                    else:
                        walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(json.loads((path or self.path).read_text(encoding="utf-8")))
        return found

    def backups(self):
        return list(self.tmp.glob("hooks.json.bak-*"))

    def test_dry_run_reports_without_writing(self):
        before = self.path.read_text(encoding="utf-8")
        code, out, _ = run("--path", str(self.path))
        self.assertEqual(code, 0)
        self.assertIn("--apply", out)
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)
        self.assertEqual(self.backups(), [])

    def test_apply_unquotes_every_command(self):
        code, _, _ = run("--path", str(self.path), "--apply")
        self.assertEqual(code, 0)
        for command in self.commands():
            self.assertNotIn('"', command)
        self.assertEqual(
            sorted(self.commands()),
            sorted(
                [
                    "python C:\\Users\\me\\.claude\\hooks\\danger_zone_guard.py",
                    "python3 /home/me/hooks/lint_gate.py",
                ]
            ),
        )

    def test_apply_leaves_valid_json_and_preserves_structure(self):
        run("--path", str(self.path), "--apply")
        fixed = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(set(fixed), set(BROKEN))
        self.assertTrue(fixed["danger-zone-guard"]["enabled"])
        self.assertEqual(
            fixed["danger-zone-guard"]["PreToolUse"][0]["matcher"], "run_command"
        )
        self.assertEqual(fixed["lint-gate"]["Stop"][0]["timeout"], 60)

    def test_apply_writes_a_backup_of_the_original(self):
        original = self.path.read_text(encoding="utf-8")
        run("--path", str(self.path), "--apply")
        backups = self.backups()
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), original)

    def test_running_twice_is_idempotent(self):
        run("--path", str(self.path), "--apply")
        after_first = self.path.read_text(encoding="utf-8")
        code, out, _ = run("--path", str(self.path), "--apply")
        self.assertEqual(code, 0)
        self.assertIn("nothing to fix", out)
        self.assertEqual(self.path.read_text(encoding="utf-8"), after_first)
        # The no-op run must not pile up backups either.
        self.assertEqual(len(self.backups()), 1)

    def test_already_correct_file_is_left_alone(self):
        self.write(
            {
                "ok": {
                    "Stop": [
                        {"type": "command", "command": "python /home/me/hooks/x.py"}
                    ]
                }
            }
        )
        before = self.path.read_text(encoding="utf-8")
        code, out, _ = run("--path", str(self.path), "--apply")
        self.assertEqual(code, 0)
        self.assertIn("nothing to fix", out)
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_non_python_commands_are_not_touched(self):
        # Only interpreter invocations are in scope. A quoted argument to some
        # other program may well be intentional, so the script must not guess.
        self.write(
            {
                "other": {
                    "Stop": [
                        {"type": "command", "command": 'node "/home/me/hooks/x.js"'}
                    ]
                }
            }
        )
        before = self.path.read_text(encoding="utf-8")
        code, out, _ = run("--path", str(self.path), "--apply")
        self.assertEqual(code, 0)
        self.assertIn("nothing to fix", out)
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)

    def test_invalid_json_is_refused_rather_than_rewritten(self):
        self.path.write_text("{ not json", encoding="utf-8")
        code, _, err = run("--path", str(self.path), "--apply")
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "{ not json")
        self.assertEqual(self.backups(), [])

    def test_missing_file_exits_non_zero(self):
        code, _, err = run("--path", str(self.tmp / "nope.json"), "--apply")
        self.assertEqual(code, 2)
        self.assertIn("not found", err)


class ShippedTemplateTests(unittest.TestCase):
    """The shipped example must be what the script considers already correct."""

    def test_hooks_example_needs_no_repair(self):
        example = REPO / "antigravity" / "templates" / "hooks-example.json"
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "hooks.json"
            copy.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
            code, out, _ = run("--path", str(copy), "--apply")
        self.assertEqual(code, 0)
        self.assertIn("nothing to fix", out)


if __name__ == "__main__":
    unittest.main()
