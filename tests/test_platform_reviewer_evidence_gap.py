"""Offline contract tests for evidence-gap sync across non-Codex platforms."""

import re
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class PlatformSpec:
    name: str
    reviewer: Path
    role_contracts: Path
    skill: Path
    required_frontmatter: tuple[str, ...]
    forbidden_patterns: tuple[str, ...]


ADOPTED_PLATFORMS = (
    PlatformSpec(
        name="claude",
        reviewer=ROOT / "claude/plugins/agent-advisor-claude/agents/advisor-opus-reviewer.md",
        role_contracts=ROOT / "claude/plugins/agent-advisor-claude/skills/orchestration/references/role-contracts.md",
        skill=ROOT / "claude/plugins/agent-advisor-claude/skills/orchestration/SKILL.md",
        required_frontmatter=(
            r"^model:\s+opus\s*$",
            r"^tools:\s+Read, Glob, Grep, Bash\s*$",
            r"^disallowedTools:\s+Agent, Edit, Write\s*$",
        ),
        forbidden_patterns=(r"(?m)^readonly:", r"(?m)^commandExecutionPolicy:", r"\bSOL REVIEW\b"),
    ),
    PlatformSpec(
        name="cursor",
        reviewer=ROOT / "cursor/plugins/agent-advisor-cursor/agents/advisor-opus-reviewer.md",
        role_contracts=ROOT / "cursor/plugins/agent-advisor-cursor/skills/orchestration/references/role-contracts.md",
        skill=ROOT / "cursor/plugins/agent-advisor-cursor/skills/orchestration/SKILL.md",
        required_frontmatter=(
            r"^model:\s+claude-opus-5-5-high\s*$",
            r"^readonly:\s+true\s*$",
        ),
        forbidden_patterns=(r"(?m)^tools:", r"(?m)^commandExecutionPolicy:", r"\bSOL REVIEW\b"),
    ),
    PlatformSpec(
        name="antigravity",
        reviewer=ROOT / "antigravity/plugins/agent-advisor-antigravity/agents/advisor-pro-reviewer.md",
        role_contracts=ROOT / "antigravity/plugins/agent-advisor-antigravity/skills/orchestration/references/role-contracts.md",
        skill=ROOT / "antigravity/plugins/agent-advisor-antigravity/skills/orchestration/SKILL.md",
        required_frontmatter=(
            r"^model:\s+pro\s*$",
            r"^mainAgent:\s+false\s*$",
            r"^subagent:\s+true\s*$",
            r"^commandExecutionPolicy:\s+off\s*$",
        ),
        forbidden_patterns=(r"(?m)^tools:", r"(?m)^readonly:", r"\bSOL REVIEW\b"),
    ),
)

HERMES_ROOT = ROOT / "hermes"


def extract_finding_contract(text: str) -> str:
    marker = "Finding evidence contract:\n"
    if marker not in text:
        return ""
    section = text.split(marker, 1)[1]
    return section.split("\n\n", 1)[0].strip()


class PlatformReviewerEvidenceGapTests(unittest.TestCase):
    def test_adopted_platforms_preserve_native_isolation_and_three_verdicts(self):
        for spec in ADOPTED_PLATFORMS:
            reviewer_text = spec.reviewer.read_text(encoding="utf-8")
            contracts_text = spec.role_contracts.read_text(encoding="utf-8")
            with self.subTest(platform=spec.name):
                for pattern in spec.required_frontmatter:
                    self.assertRegex(reviewer_text, re.compile(pattern, re.MULTILINE))
                for forbidden in spec.forbidden_patterns:
                    self.assertNotRegex(reviewer_text, forbidden)
                    self.assertNotRegex(contracts_text, forbidden)
                self.assertIn(
                    "Return exactly one verdict: `ship`, `fix-first`, or `rethink`, followed by concise,\nevidence-backed findings.",
                    reviewer_text,
                )
                self.assertIn(
                    "exactly one verdict: `ship`, `fix-first`, or `rethink`, followed by\nconcise, evidence-backed findings.",
                    contracts_text,
                )

    def test_adopted_platforms_keep_reviewer_and_review_packet_contract_in_sync(self):
        for spec in ADOPTED_PLATFORMS:
            reviewer_policy = extract_finding_contract(spec.reviewer.read_text(encoding="utf-8"))
            packet_policy = extract_finding_contract(spec.role_contracts.read_text(encoding="utf-8"))
            with self.subTest(platform=spec.name):
                self.assertTrue(reviewer_policy)
                self.assertEqual(reviewer_policy, packet_policy)

    def test_unresolved_unknown_blocks_ship_across_adopted_platforms(self):
        required_guards = (
            "Unknown is neither a confirmed defect nor proof of safety.",
            "Unresolved decisive `needs_validation` blocks `ship`.",
            "Never substitute a speculative code fix for missing evidence.",
            "An unverified control is not enough to downgrade a candidate to `hardening`.",
            "`ship` requires no required corrections and no unresolved decisive evidence gaps.",
        )
        shortcut_regex = re.compile(
            r"(?i)(?:if\b[^.\n]*needs_validation[^.\n]*,\s*ship\b"
            r"|needs_validation[^.\n]*(?:may|can|allows?|permits?)\s+(?:\w+\s+)?ship\b"
            r"|ship\s+is\s+(?:allowed|permitted)[^.\n]*needs_validation)"
        )
        for spec in ADOPTED_PLATFORMS:
            reviewer_text = spec.reviewer.read_text(encoding="utf-8")
            contracts_text = spec.role_contracts.read_text(encoding="utf-8")
            skill_text = spec.skill.read_text(encoding="utf-8")
            with self.subTest(platform=spec.name):
                for source_name, raw in (
                    ("reviewer", reviewer_text),
                    ("role-contracts", contracts_text),
                ):
                    normalized = " ".join(raw.split())
                    for guard in required_guards:
                        with self.subTest(source=source_name, guard=guard):
                            self.assertIn(guard, normalized)
                self.assertIn("Unresolved decisive `needs_validation` findings block `ship`", " ".join(skill_text.split()))
                for source_name, raw in (
                    ("reviewer", reviewer_text),
                    ("role-contracts", contracts_text),
                    ("skill", skill_text),
                ):
                    with self.subTest(source=source_name):
                        self.assertNotRegex(raw, shortcut_regex)

    def test_validation_only_fix_first_requires_fresh_review_and_blocks_self_clear(self):
        for spec in ADOPTED_PLATFORMS:
            contracts_text = " ".join(spec.role_contracts.read_text(encoding="utf-8").split())
            skill_text = " ".join(spec.skill.read_text(encoding="utf-8").split())
            with self.subTest(platform=spec.name):
                for source_name, text in (("role-contracts", contracts_text), ("skill", skill_text)):
                    with self.subTest(source=source_name):
                        self.assertIn("`needs_validation`-only `fix-first`", text)
                        self.assertIn("gives its evidence to a new fresh reviewer for a new verdict", text)
                        self.assertIn("not self-clear the gap or report completion without that verdict", text)

    def test_hermes_remains_skill_only_without_reviewer_role_or_verdict_contract(self):
        self.assertFalse((HERMES_ROOT / "skills/agent-advisor-orchestration/agents").exists())
        self.assertFalse((HERMES_ROOT / "skills/agent-advisor-orchestration/references/role-contracts.md").exists())
        skill_text = (HERMES_ROOT / "skills/agent-advisor-orchestration/SKILL.md").read_text(encoding="utf-8")
        for verdict in ("fix-first", "rethink", "Finding evidence contract"):
            with self.subTest(verdict=verdict):
                self.assertNotIn(verdict, skill_text)


if __name__ == "__main__":
    unittest.main()
