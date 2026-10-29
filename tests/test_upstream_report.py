"""Tests for codex/tools/check_upstream_updates.py report rendering.

The report is committed, and CI runs `git diff --check`, which rejects a blank
line at end of file. Every section ends with a blank separator, so the renderer
has to trim it; these tests pin that for both the normal and the failure path.
"""

import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "codex" / "tools" / "check_upstream_updates.py"

spec = importlib.util.spec_from_file_location("check_upstream_updates", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

BASELINE = {
    "repo": "https://example.invalid/upstream.git",
    "branch": "main",
    "reviewed_through": "0123456789abcdef",
    "reviewed_date": "2026-09-30",
    "reviewed_pr_through": 3,
    "reviewed_issue_through": 4,
}


class ReportEndsWithSingleNewline(unittest.TestCase):
    def assert_single_trailing_newline(self, text):
        self.assertTrue(text.endswith("\n"))
        self.assertFalse(text.endswith("\n\n"), "a blank line at EOF fails git diff --check")

    def test_report_with_nothing_pending(self):
        self.assert_single_trailing_newline(checker.render_markdown(BASELINE, [], [], [], None))

    def test_report_when_the_check_failed(self):
        self.assert_single_trailing_newline(checker.render_markdown(BASELINE, [], None, None, "boom"))


class UpstreamInputRegressionTests(unittest.TestCase):
    def test_commit_report_preserves_complete_filenames(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def git(*args):
                return subprocess.run(
                    ["git", *args], cwd=root, check=True, capture_output=True,
                    text=True, encoding="utf-8",
                ).stdout.strip()

            git("init", "--quiet")
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "--quiet", "--allow-empty",
                "-m", "baseline")
            baseline = {**BASELINE, "reviewed_through": git("rev-parse", "HEAD")}
            filenames = ["file with spaces.txt", "中文.txt"]
            for name in filenames:
                (root / name).write_text("fixture\n", encoding="utf-8")
            git("add", "--", *filenames)
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "filenames")
            git("update-ref", checker.UPSTREAM_REF, "HEAD")
            with patch.object(checker, "REPO_ROOT", root):
                commits = checker.collect_new_commits(baseline)

        self.assertEqual(len(commits), 1)
        self.assertCountEqual(commits[0]["files"], filenames)
        report = checker.render_markdown(baseline, commits, [], [], None)
        for name in filenames:
            self.assertIn(name, report)

    def test_invalid_baseline_types_return_field_error_without_traceback(self):
        valid = {**BASELINE, "reviewed_through": "a" * 40}
        cases = [("baseline", [])]
        for field in checker.REQUIRED_FIELDS:
            for value in (42, True, [], {}):
                cases.append((field, {**valid, field: value}))
        for field in ("reviewed_pr_through", "reviewed_issue_through"):
            for value in ("bad", "3", [], {}, True, 1.5, None, -1):
                cases.append((field, {**valid, field: value}))

        with tempfile.TemporaryDirectory() as directory:
            baseline_path = Path(directory) / "baseline.json"
            output = Path(directory) / "report.md"
            original_load = checker.load_baseline
            for field, payload in cases:
                with self.subTest(field=field, payload=payload):
                    baseline_path.write_text(json.dumps(payload), encoding="utf-8")
                    stdout = io.StringIO()
                    with (
                        patch.object(checker, "load_baseline",
                                     side_effect=lambda: original_load(baseline_path)),
                        patch.object(checker, "fetch_upstream") as fetch,
                        patch.object(checker, "collect_new_commits", return_value=[]),
                        patch.object(checker, "collect_new_tickets", return_value=[]),
                        redirect_stdout(stdout),
                    ):
                        result = checker.main(["--output", str(output)])
                    self.assertEqual(result, 2)
                    self.assertIn(field, stdout.getvalue())
                    self.assertIn("Check failed", output.read_text(encoding="utf-8"))
                    self.assertNotIn("Traceback", stdout.getvalue())
                    fetch.assert_not_called()

    def test_optional_watermarks_may_be_absent_or_zero(self):
        baseline = {**BASELINE, "reviewed_through": "a" * 40}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "baseline.json"
            for include in (False, True):
                payload = dict(baseline)
                for field in ("reviewed_pr_through", "reviewed_issue_through"):
                    if include:
                        payload[field] = 0
                    else:
                        payload.pop(field, None)
                path.write_text(json.dumps(payload), encoding="utf-8")
                self.assertEqual(checker.load_baseline(path), payload)


if __name__ == "__main__":
    unittest.main()
