#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ag_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
repo_root=$(CDPATH= cd -- "$ag_root/.." && pwd)

python3 - "$repo_root" "$ag_root" <<'PY'
import json
import pathlib
import re
import sys

repo = pathlib.Path(sys.argv[1])
ag = pathlib.Path(sys.argv[2])
plugin = ag / "plugins" / "agent-advisor-antigravity"

required = [
    plugin / "plugin.json",
    plugin / "LICENSE",
    plugin / "skills" / "orchestration" / "SKILL.md",
    plugin / "skills" / "orchestration" / "references" / "operations.md",
    plugin / "skills" / "orchestration" / "references" / "role-contracts.md",
    plugin / "rules" / "selective-routing.md",
    ag / "README.md",
    ag / "docs" / "WORKFLOW.zh-TW.md",
    ag / "templates" / "README.md",
    ag / "templates" / "AGENTS.md.snippet.md",
    ag / "templates" / "hooks-example.json",
    ag / "scripts" / "fix_hook_quoting.py",
]
for path in required:
    assert path.is_file(), f"required file missing: {path}"

manifest = json.loads(required[0].read_text(encoding="utf-8"))
assert manifest["name"] == "agent-advisor-antigravity"
# The manifest must sit at the plugin root: Antigravity does not read .claude-plugin/.
assert not (plugin / ".claude-plugin").exists()
assert not (plugin / ".cursor-plugin").exists()
print("PASS: Antigravity plugin manifest and root placement")

agents = plugin / "agents"
expected = {
    "advisor-flash-implementer.md": "flash",
    "advisor-pro-implementer.md": "pro",
    "advisor-pro-reviewer.md": "pro",
}
assert {p.name for p in agents.glob("*.md")} == set(expected)
for name, tier in expected.items():
    text = (agents / name).read_text(encoding="utf-8")
    # model takes a tier, never a dated model ID.
    assert re.search(rf"^model:\s+{tier}\s*$", text, re.M), name
    assert re.search(r"^name:\s+[a-z0-9-]+\s*$", text, re.M), name
    assert re.search(r"^subagent:\s+true\s*$", text, re.M), name
    assert re.search(r"^mainAgent:\s+false\s*$", text, re.M), name
reviewer = (agents / "advisor-pro-reviewer.md").read_text(encoding="utf-8")
assert re.search(r"^commandExecutionPolicy:\s+off\s*$", reviewer, re.M)
assert "Return exactly one verdict" in reviewer
# The tools vocabulary is undocumented; a guessed identifier must never be shipped.
assert not re.search(r"^tools:", reviewer, re.M)
print("PASS: Antigravity agent inventory, model tiers, and reviewer execution policy")

rule = (plugin / "rules" / "selective-routing.md").read_text(encoding="utf-8")
assert not rule.lstrip().startswith("---"), "GEMINI.md/AGENTS.md-style rules take no frontmatter"
assert "SELECTIVE ROUTE" in rule
print("PASS: Antigravity always-active rule")

skill = (plugin / "skills" / "orchestration" / "SKILL.md").read_text(encoding="utf-8")
for needle in (
    "SELECTIVE ROUTE",
    "mode: solo | delegate | audit | full",
    "advisor-flash-implementer",
    "advisor-pro-implementer",
    "advisor-pro-reviewer",
    "rules/selective-routing.md",
):
    assert needle in skill, needle
for path in ag.rglob("*"):
    if path.is_file() and path.parent.name != "scripts":
        assert path.suffix != ".toml", path
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert "agent-advisor-claude" not in text, path
        assert "agent-advisor-cursor" not in text, path
        assert "alwaysApply" not in text, path
print("PASS: Antigravity routing and platform-separation contracts")

# Antigravity splits a hook command into argv itself: a quoted script path keeps its
# quotes inside the filename and fails with [Errno 22]. The example must never regress
# to the shell-style quoted form that is correct for Claude Code.
hooks_example = json.loads((ag / "templates" / "hooks-example.json").read_text(encoding="utf-8"))
commands = []

def collect(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "command" and isinstance(value, str):
                commands.append(value)
            else:
                collect(value)
    elif isinstance(node, list):
        for item in node:
            collect(item)

collect(hooks_example)
assert commands, "hooks example declares no hook command"
for command in commands:
    assert '"' not in command, f"hook path must not be quoted: {command}"
    assert command.startswith("python "), f"hook must invoke python, not a bare bash: {command}"
    assert " " not in command.split(" ", 1)[1], f"no shell means no spaces in the path: {command}"
    assert "<you>" in command, f"template must use the generic placeholder: {command}"

fixer = (ag / "scripts" / "fix_hook_quoting.py").read_text(encoding="utf-8")
compile(fixer, "fix_hook_quoting.py", "exec")
assert "--apply" in fixer, "the repair script must default to a dry run"
assert "shutil.copy2" in fixer, "the repair script must back up before writing"
print("PASS: Antigravity hook command shape and repair script")

print("ANTIGRAVITY VERIFY PASSED")
PY
