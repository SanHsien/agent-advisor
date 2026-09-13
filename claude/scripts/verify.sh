#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
claude_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
repo_root=$(CDPATH= cd -- "$claude_root/.." && pwd)

python3 - "$repo_root" "$claude_root" <<'PY'
import json
import pathlib
import re
import sys

repo = pathlib.Path(sys.argv[1])
claude = pathlib.Path(sys.argv[2])
plugin = claude / "plugins" / "agent-advisor-claude"

required = [
    repo / ".claude-plugin" / "marketplace.json",
    claude / ".claude-plugin" / "marketplace.json",
    plugin / ".claude-plugin" / "plugin.json",
    plugin / "LICENSE",
    plugin / "skills" / "orchestration" / "SKILL.md",
    plugin / "skills" / "orchestration" / "references" / "operations.md",
    plugin / "skills" / "orchestration" / "references" / "role-contracts.md",
    claude / "README.md",
    claude / "docs" / "WORKFLOW.zh-TW.md",
]
for path in required:
    assert path.is_file(), f"required file missing: {path}"

root_market = json.loads(required[0].read_text(encoding="utf-8"))
local_market = json.loads(required[1].read_text(encoding="utf-8"))
manifest = json.loads(required[2].read_text(encoding="utf-8"))
assert root_market["name"] == "agent-advisor"
assert root_market["plugins"][0]["source"] == "./claude/plugins/agent-advisor-claude"
assert local_market["plugins"][0]["source"] == "./plugins/agent-advisor-claude"
assert manifest["name"] == "agent-advisor-claude"
assert manifest["version"] == "1.0.0"
assert manifest["repository"] == "https://github.com/SanHsien/agent-advisor"
print("PASS: Claude marketplace and plugin JSON")

agents = plugin / "agents"
expected = {
    "advisor-haiku-implementer.md": "haiku",
    "advisor-sonnet-implementer.md": "sonnet",
    "advisor-opus-reviewer.md": "opus",
}
assert {p.name for p in agents.glob("*.md")} == set(expected)
for name, model in expected.items():
    text = (agents / name).read_text(encoding="utf-8")
    assert re.search(rf"^model:\s+{model}\s*$", text, re.M), name
    assert re.search(r"^name:\s+[a-z0-9-]+\s*$", text, re.M), name
reviewer = (agents / "advisor-opus-reviewer.md").read_text(encoding="utf-8")
assert re.search(r"^tools:\s+Read, Glob, Grep, Bash\s*$", reviewer, re.M)
assert re.search(r"^disallowedTools:.*Edit.*Write", reviewer, re.M)
assert "Return exactly one verdict" in reviewer
print("PASS: Claude native agent inventory, model aliases, and reviewer restrictions")

skill = (plugin / "skills" / "orchestration" / "SKILL.md").read_text(encoding="utf-8")
for needle in (
    "SELECTIVE ROUTE",
    "mode: solo | delegate | audit | full",
    "agent-advisor-claude:advisor-haiku-implementer",
    "agent-advisor-claude:advisor-sonnet-implementer",
    "agent-advisor-claude:advisor-opus-reviewer",
    "substitution warning",
    "git status --short",
):
    assert needle in skill, needle
for path in claude.rglob("*"):
    if path.is_file():
        assert path.suffix != ".toml", path
        assert not path.name.startswith("inspect-primary-attestation"), path
print("PASS: Claude routing and platform-separation contracts")

templates = claude / "templates"
activation = claude / "docs" / "ACTIVATION.zh-TW.md"
snippet = templates / "claude-md-snippet.md"
example = templates / "settings-example.json"
hook = templates / "session-start-activation.py"
for path in (activation, templates / "README.md", snippet, example, hook):
    assert path.is_file(), f"activation asset missing: {path}"

settings = json.loads(example.read_text(encoding="utf-8"))
assert settings["model"].startswith("claude-opus-"), settings["model"]
assert settings["effortLevel"] in {"low", "medium", "high", "xhigh", "max"}
hook_command = settings["hooks"]["SessionStart"][0]["hooks"][0]["command"]
assert hook_command.startswith("python "), hook_command
assert hook.name in hook_command, hook_command

snippet_text = snippet.read_text(encoding="utf-8")
for needle in (
    "agent-advisor-claude:orchestration",
    "SELECTIVE ROUTE",
    "solo",
    "delegate",
    "audit",
    "full",
):
    assert needle in snippet_text, needle
# A user who has not restarted yet must not be told to raise an error.
assert "不報錯" in snippet_text
assert "without raising an error" in snippet_text

compile(hook.read_text(encoding="utf-8"), str(hook), "exec")
assert "additionalContext" in hook.read_text(encoding="utf-8")

# Templates are copied into someone else's home directory: keep them generic.
for path in templates.rglob("*"):
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        assert "Users\\SanHsien" not in text, path
        assert "Users/SanHsien" not in text, path
        assert "<you>" in text or "Users" not in text, path
print("PASS: Claude activation guide and copy-paste templates")

print("CLAUDE VERIFY PASSED")
PY
