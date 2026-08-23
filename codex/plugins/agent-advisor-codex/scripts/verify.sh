#!/bin/sh
set -eu

pass() { printf '%s\n' "PASS: $*"; }
fail() { printf '%s\n' "FAIL: $*" >&2; exit 1; }
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
plugin_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
codex_root=$(CDPATH= cd -- "$plugin_dir/../.." && pwd)
repo_root=$(CDPATH= cd -- "$codex_root/.." && pwd)
installer=$script_dir/install-agents.sh
inspector=$script_dir/inspect-primary-attestation.sh
model_hook=$plugin_dir/hooks/observe_primary_model.py
hooks_config=$plugin_dir/hooks/hooks.json

for path in \
  "$repo_root/.agents/plugins/marketplace.json" \
  "$codex_root/.agents/plugins/marketplace.json" \
  "$plugin_dir/.codex-plugin/plugin.json" \
  "$plugin_dir/LICENSE" \
  "$plugin_dir/skills/orchestration/SKILL.md" \
  "$installer" "$inspector" "$model_hook" "$hooks_config"
do
  [ -f "$path" ] || fail "required file missing: $path"
done

python3 - "$repo_root" "$codex_root" "$plugin_dir" <<'PY'
import json
import pathlib
import sys
import tomllib

repo = pathlib.Path(sys.argv[1])
codex = pathlib.Path(sys.argv[2])
plugin = pathlib.Path(sys.argv[3])
root_market = json.loads((repo / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
local_market = json.loads((codex / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
assert root_market["name"] == "agent-advisor"
assert root_market["plugins"][0]["name"] == "agent-advisor-codex"
assert root_market["plugins"][0]["source"]["path"] == "./codex/plugins/agent-advisor-codex"
assert local_market["plugins"][0]["source"]["path"] == "./plugins/agent-advisor-codex"
assert manifest["name"] == "agent-advisor-codex"
assert manifest["version"] == "1.0.0"
assert manifest["interface"]["displayName"] == "Agent Advisor for Codex"
assert manifest["author"]["name"] == "Daniel McAteer"

expected = {
    "agent-advisor-codex-luna-implementer.toml": ("agent_advisor_codex_luna_implementer", "gpt-5.6-luna", "max"),
    "agent-advisor-codex-terra-implementer.toml": ("agent_advisor_codex_terra_implementer", "gpt-5.6-terra", "high"),
    "agent-advisor-codex-sol-reviewer.toml": ("agent_advisor_codex_sol_reviewer", "gpt-5.6-sol", "high"),
}
agents = plugin / "agents"
assert {p.name for p in agents.glob("*.toml")} == set(expected)
for name, values in expected.items():
    data = tomllib.loads((agents / name).read_text(encoding="utf-8"))
    assert (data["name"], data["model"], data["model_reasoning_effort"]) == values
reviewer = tomllib.loads((agents / "agent-advisor-codex-sol-reviewer.toml").read_text(encoding="utf-8"))
assert reviewer["sandbox_mode"] == "read-only"
print("PASS: Codex JSON/TOML manifests and exact role contract")
PY

skill=$plugin_dir/skills/orchestration/SKILL.md
operations=$plugin_dir/skills/orchestration/references/operations.md
for needle in \
  'SELECTIVE ROUTE' \
  'mode: solo | delegate | audit | full' \
  'AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION: gpt-5.6-sol/high'
do
  grep -Fq "$needle" "$skill" || fail "skill omits: $needle"
done
for role_id in agent_advisor_codex_luna_implementer agent_advisor_codex_terra_implementer agent_advisor_codex_sol_reviewer; do
  grep -Fq "$role_id" "$operations" || fail "operations reference omits: $role_id"
done
pass 'Codex routing and primary-attestation contracts'

tmp_base=${TMPDIR:-/tmp}
case "$tmp_base" in /*) ;; *) tmp_base=/tmp ;; esac
tmp_dir=$(mktemp -d "$tmp_base/agent-advisor-codex-verify.XXXXXX") || fail 'could not create fixture directory'
cleanup() { rm -rf -- "$tmp_dir"; }
trap cleanup EXIT HUP INT TERM

attestation_home=$tmp_dir/home
mkdir -p -- "$attestation_home"
printf '%s\n' 'AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION: gpt-5.6-sol/high' > "$attestation_home/AGENTS.md"
output=$(CODEX_HOME="$attestation_home" sh "$inspector")
printf '%s\n' "$output" | grep -Fq 'PRIMARY_ATTESTATION PASSED' || fail 'valid primary attestation was refused'
printf '%s\n' "$output" | grep -Fq 'provenance=user-level-file' || fail 'inspector omitted verified provenance'

clean=$tmp_dir/clean
sh "$installer" --target-dir "$clean"
sh "$installer" --target-dir "$clean" --check
sh "$installer" --target-dir "$clean" --check-role luna --check-role sol
printf '%s\n' modified >> "$clean/agent-advisor-codex-terra-implementer.toml"
if sh "$installer" --target-dir "$clean" --check-role terra >/dev/null 2>&1; then fail 'modified Terra role was accepted'; fi
sh "$installer" --target-dir "$clean" --check-role luna --check-role sol
if sh "$installer" --target-dir "$clean" >/dev/null 2>&1; then fail 'conflicting install was accepted'; fi
pass 'Codex inspector and fail-closed installer fixtures'

sh -n "$installer"
sh -n "$inspector"
sh -n "$script_dir/inspect-agent-runtime.sh"
pass 'Codex shell syntax'
printf '%s\n' 'CODEX VERIFY PASSED'
