#!/bin/sh

set -eu

fail() { printf '%s\n' "PRIMARY_ATTESTATION REFUSED: $*" >&2; exit 1; }

marker='AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION: gpt-5.6-sol/high'

[ "$#" -eq 0 ] || fail 'path arguments are not accepted'
if [ -n "${CODEX_HOME:-}" ]; then
  codex_home=$CODEX_HOME
else
  [ -n "${HOME:-}" ] || fail 'HOME is unavailable'
  codex_home=$HOME/.codex
fi

agents=$codex_home/AGENTS.md
override=$codex_home/AGENTS.override.md

[ ! -e "$override" ] || fail "user-level override exists: $override"
[ -f "$agents" ] || fail "regular user-level AGENTS.md is missing: $agents"
[ ! -L "$agents" ] || fail "user-level AGENTS.md is a symlink: $agents"

size=$(wc -c < "$agents" | tr -d '[:space:]')
[ "$size" -le 32768 ] || fail "user-level AGENTS.md exceeds 32768 bytes: $agents"

count=$(awk -v marker="$marker" '{ sub(/\r$/, ""); if ($0 == marker) count++ } END { print count + 0 }' "$agents")
[ "$count" -eq 1 ] || fail "expected exactly one attestation marker, found $count"

printf '%s\n' \
  'PRIMARY_ATTESTATION PASSED' \
  "source=$agents" \
  'provenance=user-level-file' \
  'model=gpt-5.6-sol' \
  'effort=high'
