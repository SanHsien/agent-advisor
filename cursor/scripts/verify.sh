#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cursor_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
repo_root=$(CDPATH= cd -- "$cursor_root/.." && pwd)

python3 - "$repo_root" "$cursor_root" <<'PY'
import json
import pathlib
import re
import sys

repo = pathlib.Path(sys.argv[1])
cursor = pathlib.Path(sys.argv[2])
plugin = cursor / "plugins" / "agent-advisor-cursor"

required = [
    plugin / ".cursor-plugin" / "plugin.json",
    plugin / "LICENSE",
    plugin / "skills" / "orchestration" / "SKILL.md",
    plugin / "skills" / "orchestration" / "references" / "operations.md",
    plugin / "skills" / "orchestration" / "references" / "role-contracts.md",
    plugin / "rules" / "selective-routing.mdc",
    cursor / "README.md",
    cursor / "docs" / "WORKFLOW.zh-TW.md",
]
for path in required:
    assert path.is_file(), f"required file missing: {path}"

manifest = json.loads(required[0].read_text(encoding="utf-8"))
assert manifest["name"] == "agent-advisor-cursor"
assert manifest["version"] == "1.0.0"
print("PASS: Cursor plugin manifest")

agents = plugin / "agents"
expected = {
    "advisor-composer-implementer.md": "composer-2.5",
    "advisor-sonnet-implementer.md": "claude-sonnet-5-thinking-high",
    "advisor-opus-reviewer.md": "claude-opus-5-thinking-high",
}
assert {p.name for p in agents.glob("*.md")} == set(expected)
for name, model in expected.items():
    text = (agents / name).read_text(encoding="utf-8")
    assert re.search(rf"^model:\s+{re.escape(model)}\s*$", text, re.M), name
    assert re.search(r"^name:\s+[a-z0-9-]+\s*$", text, re.M), name
    assert re.search(r"^description:\s+\S", text, re.M), name
# Cursor has no tool allowlist: the reviewer's isolation is the readonly flag.
reviewer = (agents / "advisor-opus-reviewer.md").read_text(encoding="utf-8")
assert re.search(r"^readonly:\s+true\s*$", reviewer, re.M)
assert "Return exactly one verdict" in reviewer
for name in ("advisor-composer-implementer.md", "advisor-sonnet-implementer.md"):
    assert re.search(r"^readonly:\s+false\s*$", (agents / name).read_text(encoding="utf-8"), re.M), name
print("PASS: Cursor agent inventory, pinned models, and reviewer readonly flag")

rule = (plugin / "rules" / "selective-routing.mdc").read_text(encoding="utf-8")
assert re.search(r"^alwaysApply:\s+true\s*$", rule, re.M), "activation rule must always apply"
assert re.search(r"^description:\s+\S", rule, re.M)
assert "SELECTIVE ROUTE" in rule
print("PASS: Cursor always-apply activation rule")

skill = (plugin / "skills" / "orchestration" / "SKILL.md").read_text(encoding="utf-8")
for needle in (
    "SELECTIVE ROUTE",
    "mode: solo | delegate | audit | full",
    "advisor-composer-implementer",
    "advisor-sonnet-implementer",
    "advisor-opus-reviewer",
    "rules/selective-routing.mdc",
):
    assert needle in skill, needle
# Platform separation: no Codex TOML, no Claude Code runtime contracts.
# The verifiers themselves name the forbidden strings, so they are not scanned.
for path in cursor.rglob("*"):
    if path.is_file() and path.parent.name != "scripts":
        assert path.suffix != ".toml", path
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert "agent-advisor-claude" not in text, path
        assert "permissionMode" not in text, path
print("PASS: Cursor routing and platform-separation contracts")
print("CURSOR VERIFY PASSED")
PY
