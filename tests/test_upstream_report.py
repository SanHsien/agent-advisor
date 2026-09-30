"""Tests for codex/tools/check_upstream_updates.py report rendering.

The report is committed, and CI runs `git diff --check`, which rejects a blank
line at end of file. Every section ends with a blank separator, so the renderer
has to trim it; these tests pin that for both the normal and the failure path.
"""

import importlib.util
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
