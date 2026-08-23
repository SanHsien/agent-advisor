from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from codex.tools import check_upstream_updates as checker


class CollectNewTicketsTests(unittest.TestCase):
    @patch("codex.tools.check_upstream_updates.subprocess.run")
    def test_queries_all_states_and_keeps_closed_items(self, run: Mock) -> None:
        run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(
                [
                    {"number": 25, "title": "already reviewed"},
                    {"number": 26, "title": "closed between scheduled checks"},
                ]
            ),
        )
        baseline = {
            "repo": "https://github.com/DannyMac180/sol-advisor.git",
            "reviewed_pr_through": 25,
        }

        self.assertEqual(
            checker.collect_new_tickets(baseline, "pr"),
            [{"number": 26, "title": "closed between scheduled checks"}],
        )
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--state") + 1], "all")


class MainFailureTests(unittest.TestCase):
    @patch("codex.tools.check_upstream_updates.collect_new_tickets")
    @patch("codex.tools.check_upstream_updates.collect_new_commits", return_value=[])
    @patch("codex.tools.check_upstream_updates.fetch_upstream")
    @patch("codex.tools.check_upstream_updates.load_baseline")
    def test_ticket_enumeration_failure_is_fail_closed(
        self,
        load_baseline: Mock,
        _fetch_upstream: Mock,
        _collect_new_commits: Mock,
        collect_new_tickets: Mock,
    ) -> None:
        load_baseline.return_value = {
            "repo": "https://github.com/DannyMac180/sol-advisor.git",
            "branch": "main",
            "reviewed_through": "0" * 40,
            "reviewed_date": "2026-08-23",
            "reviewed_pr_through": 24,
            "reviewed_issue_through": 25,
        }
        collect_new_tickets.side_effect = [None, []]

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.md"
            with redirect_stdout(io.StringIO()):
                result = checker.main(["--strict", "--output", str(output)])
            report = output.read_text(encoding="utf-8")

        self.assertEqual(result, 2)
        self.assertIn("Check failed", report)
        self.assertIn("could not enumerate upstream PRs", report)


if __name__ == "__main__":
    unittest.main()
