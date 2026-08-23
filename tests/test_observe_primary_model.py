"""Contract tests for the advisory primary-model hook.

The hook runs on the user's own prompts, so the properties that matter are mostly
negative: stay silent on anything unexpected, never claim more than the model
field, and never let an untrusted string reach developer context unfiltered.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

HOOK = (
    pathlib.Path(__file__).resolve().parents[1]
    / "codex"
    / "plugins"
    / "agent-advisor-codex"
    / "hooks"
    / "observe_primary_model.py"
)
HOOKS_CONFIG = HOOK.parent / "hooks.json"

_spec = importlib.util.spec_from_file_location("observe_primary_model", HOOK)
assert _spec and _spec.loader
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)

ORCHESTRATION_PROMPT = "Use $agent-advisor-codex:orchestration to plan this change."


def payload(**overrides: object) -> dict:
    base = {
        "hook_event_name": "UserPromptSubmit",
        "prompt": ORCHESTRATION_PROMPT,
        "model": "gpt-5.6-sol",
    }
    base.update(overrides)
    return base


class AdvisoryContent(unittest.TestCase):
    def test_matching_model_is_reported_as_covering_the_model_only(self) -> None:
        line = hook.advisory_for(payload())

        assert line is not None
        self.assertIn("gpt-5.6-sol", line)
        self.assertIn("model field only", line)

    def test_the_advisory_never_claims_reasoning_effort(self) -> None:
        """Hook input exposes the model, not the effort.

        An advisory that implied effort had been observed would weaken the very
        gate it exists to strengthen.
        """
        for model in ("gpt-5.6-sol", "gpt-5.6-luna"):
            line = hook.advisory_for(payload(model=model))
            assert line is not None
            for effort_claim in ("/high", "high reasoning", "reasoning effort is high"):
                self.assertNotIn(effort_claim, line)

    def test_mismatch_names_the_active_model_and_the_remedy(self) -> None:
        line = hook.advisory_for(payload(model="gpt-5.6-luna"))

        assert line is not None
        self.assertIn("gpt-5.6-luna", line)
        self.assertIn("/model", line)


class StaysSilent(unittest.TestCase):
    def test_unrelated_prompts_are_ignored(self) -> None:
        self.assertIsNone(hook.advisory_for(payload(prompt="fix the failing test")))

    def test_a_command_substring_does_not_count_as_an_invocation(self) -> None:
        self.assertIsNone(
            hook.advisory_for(prompt_payload("$agent-advisor-codex:orchestration-notes"))
        )

    def test_other_hook_events_are_ignored(self) -> None:
        self.assertIsNone(hook.advisory_for(payload(hook_event_name="SessionStart")))

    def test_a_missing_model_field_costs_nothing(self) -> None:
        """A host that does not expose the model must not break anything."""
        body = payload()
        del body["model"]

        self.assertIsNone(hook.advisory_for(body))

    def test_malformed_payloads_are_ignored(self) -> None:
        for body in (None, [], "text", {}, payload(prompt=None), payload(model=123)):
            self.assertIsNone(hook.advisory_for(body))

    def test_an_unsafe_model_string_never_reaches_developer_context(self) -> None:
        for model in ("gpt-5.6-sol; rm -rf /", "<script>", "a" * 65, ""):
            self.assertIsNone(hook.advisory_for(payload(model=model)))


class ProcessBehaviour(unittest.TestCase):
    def run_hook(self, stdin: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_the_hook_never_blocks_the_prompt(self) -> None:
        """Advisory means advisory: every input path exits 0."""
        for stdin in ("", "not json", json.dumps(payload()), json.dumps({"a": 1})):
            result = self.run_hook(stdin)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_matching_prompt_prints_one_line(self) -> None:
        result = self.run_hook(json.dumps(payload()))

        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(result.stdout.strip().splitlines()), 1)


class HookRegistration(unittest.TestCase):
    def test_hooks_json_points_at_the_script_that_exists(self) -> None:
        config = json.loads(HOOKS_CONFIG.read_text(encoding="utf-8"))
        entries = config["hooks"]["UserPromptSubmit"][0]["hooks"]

        self.assertEqual(len(entries), 1)
        self.assertIn("observe_primary_model.py", entries[0]["command"])
        self.assertTrue(HOOK.is_file())

    def test_the_hook_declares_a_timeout(self) -> None:
        """A hook on every prompt must not be able to hang the session."""
        config = json.loads(HOOKS_CONFIG.read_text(encoding="utf-8"))
        entry = config["hooks"]["UserPromptSubmit"][0]["hooks"][0]

        self.assertIsInstance(entry["timeout"], int)
        self.assertLessEqual(entry["timeout"], 10)


def prompt_payload(prompt: str) -> dict:
    return payload(prompt=prompt)


if __name__ == "__main__":
    unittest.main()
