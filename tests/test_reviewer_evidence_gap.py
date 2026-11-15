"""Offline prompt-contract checks, not a model-behavior evaluation."""

import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "codex/plugins/agent-advisor-codex"
ROLE = PLUGIN / "agents/agent-advisor-codex-sol-reviewer.toml"
CONTRACT = PLUGIN / "skills/orchestration/references/role-contracts.md"
DOC = ROOT / "docs/reviewer-evidence-gap-contract.md"


class ReviewerEvidenceGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.role = tomllib.loads(ROLE.read_text(encoding="utf-8"))
        cls.instructions = cls.role["developer_instructions"]
        cls.contract = CONTRACT.read_text(encoding="utf-8")

    def test_installed_role_and_spawn_prompt_have_identical_policy(self):
        policy = self.instructions.split("Finding evidence contract:\n", 1)[1]
        self.assertIn("Finding evidence contract:\n" + policy, self.contract)
        for guard in (
            "Unknown is neither a confirmed defect nor proof of safety.",
            "Unresolved decisive needs_validation blocks ship.",
            "Never substitute a speculative code fix for missing evidence.",
            "An unverified\n  control is not enough",
            "do not require a fix or block ship solely for hardening.",
        ):
            with self.subTest(guard=guard):
                self.assertIn(guard, policy)

    def test_existing_role_and_output_interface_are_preserved(self):
        self.assertEqual(self.role["name"], "agent_advisor_codex_sol_reviewer")
        self.assertEqual(self.role["model"], "gpt-5.6-sol")
        self.assertEqual(self.role["model_reasoning_effort"], "high")
        self.assertEqual(self.role["sandbox_mode"], "read-only")
        output = self.contract.split("\nSOL REVIEW\n", 1)[1].split("\n~~~", 1)[0]
        self.assertEqual(
            re.findall(r"^([A-Z ]+):", output, re.MULTILINE),
            ["VERDICT", "REASON", "FINDINGS", "RESIDUAL RISK"],
        )
        self.assertEqual(
            output.splitlines()[0], "VERDICT: ship | fix-first | rethink"
        )

    def test_fixed_examples_keep_finding_states_out_of_verdict(self):
        doc = DOC.read_text(encoding="utf-8")
        examples = re.findall(r"```text\n(SOL REVIEW\n.*?)\n```", doc, re.DOTALL)
        expected = [
            ("confirmed", "fix-first"),
            ("needs_validation", "fix-first"),
            ("hardening", "ship"),
            ("needs_validation", "rethink"),
        ]
        self.assertEqual(len(examples), len(expected))
        for example, (status, verdict) in zip(examples, expected, strict=True):
            with self.subTest(status=status, verdict=verdict):
                self.assertEqual(
                    re.findall(r"^VERDICT: (.+)$", example, re.MULTILINE),
                    [verdict],
                )
                self.assertIn(f"FINDINGS: [{status}]", example)
                for field in ("REASON:", "RESIDUAL RISK:"):
                    self.assertIn(field, example)
                if status == "needs_validation":
                    self.assertIn("缺失事實：", example)
                    self.assertIn("最小驗證：", example)
                    self.assertIn("預期觀察：", example)
                    self.assertNotEqual(verdict, "ship")
                elif status == "confirmed":
                    self.assertIn("重現：", example)
                    self.assertIn("影響：", example)
                else:
                    self.assertIn("阻擋證據：", example)
                    self.assertIn("選用", example)


if __name__ == "__main__":
    unittest.main()
