#!/bin/sh
set -eu

fail() { printf '%s\n' "ERROR: $*" >&2; exit 1; }
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
template_dir=$(CDPATH= cd -- "$script_dir/../agents" && pwd)
target_dir=''
target_supplied=false
check=false
selected=''

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target-dir)
      [ "$#" -ge 2 ] || fail '--target-dir requires a value.'
      target_supplied=true; target_dir=$2; shift 2 ;;
    --check) check=true; shift ;;
    --check-role)
      [ "$#" -ge 2 ] || fail '--check-role requires luna, terra, or sol.'
      case "$2" in luna|terra|sol) ;; *) fail "unknown --check-role '$2'." ;; esac
      selected="$selected $2"; check=true; shift 2 ;;
    *) fail "unknown argument: $1" ;;
  esac
done

if [ "$target_supplied" = true ]; then
  [ -n "$target_dir" ] || fail '--target-dir was explicitly supplied but is empty.'
else
  if [ -n "${CODEX_HOME-}" ]; then target_dir=$CODEX_HOME/agents
  elif [ -n "${HOME-}" ]; then target_dir=$HOME/.codex/agents
  else fail 'CODEX_HOME and HOME are unset; pass --target-dir.'
  fi
fi
case "$target_dir" in /|'') fail 'refusing a filesystem root or empty target.' ;; esac
[ ! -L "$target_dir" ] || fail "target directory is a symlink: $target_dir"
[ ! -e "$target_dir" ] || [ -d "$target_dir" ] || fail "target is not a directory: $target_dir"

role_file() {
  case "$1" in
    luna) printf '%s\n' agent-advisor-codex-luna-implementer.toml ;;
    terra) printf '%s\n' agent-advisor-codex-terra-implementer.toml ;;
    sol) printf '%s\n' agent-advisor-codex-sol-reviewer.toml ;;
    *) fail "unknown role: $1" ;;
  esac
}
state() {
  destination=$1 template=$2
  [ -e "$destination" ] || { printf '%s\n' missing; return; }
  [ -f "$destination" ] && [ ! -L "$destination" ] || { printf '%s\n' unsafe; return; }
  if cmp -s "$destination" "$template"; then printf '%s\n' current; else printf '%s\n' conflict; fi
}

roles='luna terra sol'
for role in $roles; do
  file=$(role_file "$role")
  template=$template_dir/$file
  [ -f "$template" ] && [ ! -L "$template" ] || fail "shipped template is missing or unsafe: $template"
done

if [ "$check" = true ]; then
  [ -n "$selected" ] || selected=$roles
  for role in $selected; do
    file=$(role_file "$role")
    current=$(state "$target_dir/$file" "$template_dir/$file")
    [ "$current" = current ] || fail "$role template is $current, not the current exact file: $target_dir/$file"
  done
  printf '%s\n' 'CHECK PASSED: selected Agent Advisor for Codex role templates exactly match shipped templates.'
  exit 0
fi

for role in $roles; do
  file=$(role_file "$role")
  current=$(state "$target_dir/$file" "$template_dir/$file")
  case "$current" in missing|current) ;; *) fail "$role destination is $current and will not be replaced: $target_dir/$file" ;; esac
done
mkdir -p -- "$target_dir"
[ -d "$target_dir" ] && [ ! -L "$target_dir" ] || fail "target directory changed after preflight: $target_dir"

for role in $roles; do
  file=$(role_file "$role")
  destination=$target_dir/$file
  template=$template_dir/$file
  current=$(state "$destination" "$template")
  if [ "$current" = current ]; then printf '%s\n' "ALREADY CURRENT: $destination"; continue; fi
  [ "$current" = missing ] || fail "$role destination changed after preflight."
  staged=$(mktemp "$target_dir/.agent-advisor-codex-agent.XXXXXX") || fail "could not stage $role"
  trap 'rm -f -- "$staged"' EXIT HUP INT TERM
  cp -- "$template" "$staged"
  [ ! -e "$destination" ] || fail "destination appeared after preflight: $destination"
  mv -- "$staged" "$destination"
  trap - EXIT HUP INT TERM
  printf '%s\n' "INSTALLED: $destination"
done

for role in $roles; do
  file=$(role_file "$role")
  [ "$(state "$target_dir/$file" "$template_dir/$file")" = current ] || fail "post-install exactness check failed: $target_dir/$file"
done
printf '%s\n' 'INSTALL PASSED: Luna, Terra, and Sol role profiles exactly match Agent Advisor for Codex.'
