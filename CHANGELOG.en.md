English | [中文版](CHANGELOG.md)

# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); newest first.
The Codex edition is derived from
[DannyMac180/sol-advisor](https://github.com/DannyMac180/sol-advisor); entries marked
`fork` describe changes relative to that upstream.

---

## 2026-08-23 (upstream PR #26 and CodeQL coverage)

### Added

- **`tools/check_links.py` and a gate for it (`fork`).** This repo is mostly documentation
  that points at itself: four editions, each with a README, docs, a plugin skill and
  reference files, all cross-linking to the root and to each other -- 49 Markdown files
  and 90 relative links. Renaming or moving a file breaks those links **silently**:
  nothing errors, the link just stops resolving, and the next reader gets a 404 instead
  of the contract they were sent to read. The check covers relative links only (external
  URLs stay a human's job, so this remains offline and deterministic) and takes its file
  list from `git ls-files`, so a local scratch file can never turn the gate red. Measured
  now: 49 files, 0 broken; injecting one broken link was confirmed to fail it. Wired into
  both `dev_check.ps1` and CI.
- **An advisory primary-model hook (`fork`, taken from upstream PR #26 and rewritten).**
  The primary's model is the one field this plugin can only take on attestation:
  `inspect-agent-runtime` reads an auxiliary's rollout, but the primary's own model and
  effort are generally unobservable from inside the session, so the gate can only label
  the result operator-attested. If the host hands the active model to a hook, that
  **one field** stops being attested and starts being observed.
  `hooks/observe_primary_model.py` does exactly that much: one advisory line when the
  prompt invokes `$agent-advisor-codex:orchestration`, silence otherwise.
  Upstream's version is shell plus `jq`. This fork is Windows-first and a default
  Windows host has no `jq` (verified here: `jq: command not found`), while `python3` is
  already a dependency of `verify.sh` -- so it is rewritten in Python: same behaviour,
  on a dependency this repo already carries.
  `tests/test_observe_primary_model.py` (13 cases) pins three properties: it **never
  blocks** (every unexpected input path exits 0 with no output, so a host that does not
  supply `model` costs nothing and the gate is unchanged), it **never claims reasoning
  effort** (hooks see the model, not the effort; implying otherwise would weaken the
  gate it exists to strengthen), and it **never authorizes orchestration**. The model
  string passes a conservative charset check before it reaches developer context --
  it is somebody else's string. Both `verify.sh` and `verify.ps1` now require the files.

### Changed

- **CodeQL now also scans `python` (`fork`).** It scanned only `actions`, on the stated
  grounds that this repo had no application code to scan. Four editions later that
  premise is gone: `antigravity/scripts/fix_hook_quoting.py` **rewrites the user's own
  hooks.json**, `claude/templates/session-start-activation.py` sits in the user's
  session-start path, and `codex/tools/check_upstream_updates.py` handles external API
  responses. All three take somebody else's data and touch somebody else's files, which
  is the shape worth scanning. Shell and PowerShell remain outside CodeQL's support and
  stay covered by the verify scripts and tests.

### Upstream

- **PR #26 judged in four parts**, one adopted (details in `docs/UPSTREAM.md`): the
  root-rollout `--primary` inspection does not apply (this fork's inspector serves
  auxiliaries only; the primary goes through attestation); reading only the latest turn
  context is **deliberately not adopted** -- a declared route must hold for the whole
  delegated run, so a mid-thread model change is contradictory evidence and taking the
  latest entry would let the contradiction pass silently (the condition that would
  change this is recorded in `docs/UPSTREAM.md`); the `configure-model-hook` skill is
  not adopted; the advisory hook is. `reviewed_pr_through` moves to 26.

## 2026-08-23 (development environment)

### Added

- **`tests/`, using stdlib `unittest` with no external dependency.** The previous change
  shipped `fix_hook_quoting.py` without tests, which was a real gap. Ten tests pin the
  contract a repair tool for a session-blocking config has to hold: a dry run writes
  nothing, `--apply` backs up first, a second run is idempotent, invalid JSON is refused
  rather than rewritten, non-Python commands are left alone, and the shipped
  `hooks-example.json` is itself already correct. Mutation-tested to confirm the tests
  actually catch regressions: removing the backup step fails 2 of them, and letting the
  dry run write fails 1.
- **Bilingual README and CHANGELOG**, matching the convention used across the other
  repositories: `README.md`/`CHANGELOG.md` in Chinese, `README.en.md`/`CHANGELOG.en.md` in
  English, cross-linked in both directions.
- **`NOTICE.md`**, separating fork attribution and license notes from the README, and
  recording which editions descend from upstream and which are new work here.

### Changed

- `tools/dev_check.ps1` and CI both run the unit tests. When python is absent locally the
  gate prints an explicit SKIP naming CI as the authority for tests, rather than passing
  silently.

## 2026-08-23 (hook quoting)

### Added

- **The Antigravity hook quoting trap, reproduced and documented.** Antigravity splits a
  hook command into argv itself instead of handing it to a shell, so a quoted script path
  keeps its quote characters inside the filename and the interpreter fails with
  `[Errno 22] Invalid argument`. Reproduced directly: passing a filename that literally
  contains quotes yields exactly that error, while the bare path runs. Claude Code passes
  hook commands to a shell, where the quoted form is correct — this is the one line that
  must not be copied between the two editions.
- **Why it is worse than an ordinary config bug.** `PreToolUse` hooks run before the tool
  does, so a broken hook fails every guarded tool call — including the ones an agent would
  use to repair the file. The observed failure mode is an agent stuck asking a human to
  fix the config by hand.
- **[`antigravity/templates/hooks-example.json`](antigravity/templates/hooks-example.json).**
  Correctly shaped blocks with the reasoning inline, including the note that with no shell
  to strip quotes there is no way to express a path containing spaces.
- **[`antigravity/scripts/fix_hook_quoting.py`](antigravity/scripts/fix_hook_quoting.py).**
  Repairs an already-broken `hooks.json`: dry run by default, backs up before writing,
  and re-parses the result. It parses JSON rather than regex-editing raw text — every path
  in that file is dense with escaped backslashes, and a pattern that misses leaves the
  hook config unparseable, which is harder to diagnose than the `Errno 22` it was meant to
  fix.

### Changed

- Both Antigravity verifiers gained a fifth gate asserting the hook example stays
  unquoted, `python`-invoked, space-free, and placeholder-only, and that the repair script
  keeps its dry-run default and its backup step.
- `claude/templates/settings-example.json` now says explicitly that its quoted form is
  correct *for Claude Code* and must not be copied into Antigravity.

## 2026-08-23 (Cursor and Antigravity editions)

### Added

- **Cursor edition (`agent-advisor-cursor`).** A Cursor-native plugin bundling the
  orchestration skill, three subagents, and an always-apply rule. Cursor subagent
  frontmatter carries `model`, `readonly`, and `is_background` but no tool allowlist, so
  reviewer isolation uses `readonly: true` — which Cursor enforces at runtime, unlike the
  Claude Code edition's prompt-level contract. Cursor has no stable family aliases, so
  each lane pins a model ID from `cursor-agent models` and fails closed when that model
  is unavailable.
- **Antigravity edition (`agent-advisor-antigravity`).** An Antigravity-native plugin
  bundle: skill, three subagents, and an always-active rule. The subagent `model` field
  takes a tier (`inherit`, `flash`, `pro`) rather than a dated ID, so lanes survive model
  releases. Validated with Antigravity's own checker: `agy plugin validate` reports 1
  skill and 3 agents processed.
- **Activation ships inside the plugin for both new editions.** Installing the plugin is
  enough to make route declaration standing behaviour — no user-level context file is
  edited, unlike the Claude Code edition. The Antigravity edition also ships an
  `AGENTS.md`/`GEMINI.md` snippet as a fallback.
- **One observed installer detail, documented so nobody re-derives it.** `agy plugin
  install` prints a component summary listing skills, agents, commands, MCP servers, and
  hooks — never rules — and `agy plugin list` reports `components: ["skills","agents"]`.
  The installer nevertheless copies the whole bundle, `rules/` included, into
  `~/.gemini/config/plugins/<name>/`, which is itself a global customization root, so the
  rule is discovered from there.

### Changed

- `tools/dev_check.ps1` and `.github/workflows/ci.yml` run the two new verifier pairs;
  the POSIX job now covers four editions.
- Root `README.md` gained both editions in the edition table, install sections, and the
  repository layout. `AGENTS.md` and `CLAUDE.md` record that each edition must express
  lane isolation with what its own runtime enforces, and must never ship a frontmatter
  field whose accepted values that runtime does not document.

### Notes

- The Antigravity reviewer deliberately ships no `tools` allowlist. The field exists in
  the schema, but the tool-name vocabulary it expects is not part of the published
  customization documentation, and a guessed identifier would silently widen or empty the
  lane's permissions. Both verifiers assert the field stays absent.

## 2026-08-23 (Claude Code persistent activation)

### Added

- **Persistent activation for the Claude Code edition.** Installing the plugin only puts
  the skill on the shelf — `orchestration` is invoked on demand like any other skill, so
  route declaration never became the default behaviour of a session. New guide
  [`claude/docs/ACTIVATION.zh-TW.md`](claude/docs/ACTIVATION.zh-TW.md) documents the
  method that makes it standing behaviour, verified on native Windows 11.
- **Copy-paste templates under [`claude/templates/`](claude/templates/README.md).** A
  `CLAUDE.md` snippet (the primary method — that file is loaded into every session, so no
  hook is required), a `settings.json` example pinning the Opus family plus `effortLevel`,
  and an optional `SessionStart` hook that injects the directive through a channel that
  survives context compaction. The hook is Python, not shell: a hook command starting with
  a bare `bash` resolves to WSL on Windows, where the home directory differs and the script
  silently never runs.
- **Manual installation path for non-TUI entrypoints.** `/plugin` is an interactive
  terminal panel and cannot open in the desktop app, VS Code, web, or SDK sessions. The
  guide records the JSON registration `/plugin install` performs — `known_marketplaces.json`
  and `installed_plugins.json` — including the hidden `.claude-plugin/` directory that must
  be copied for Claude Code to recognise the plugin at all.
- **Three documented traps that make a correct setup look broken.** A running session
  writes its own `effortLevel` back over an external edit; a launcher `--model` flag
  silently overrides `settings.json`; and `CLAUDE_CODE_EFFORT_LEVEL` locks effort for the
  whole session so the user cannot change it.
- **Session-scope table.** A change reaches new sessions and `claude --continue`/`--resume`
  sessions, but never a process that is already running: CLAUDE.md, `settings.json`, hooks,
  and the plugin list are all snapshotted at startup.

### Changed

- `claude/scripts/verify.sh` and `claude/scripts/verify.ps1` gained a fourth gate covering
  the activation assets: the files exist, the settings example stays on the Opus family with
  a supported `effortLevel`, the hook command invokes Python rather than a bare `bash`, the
  snippet keeps its four route names and its skip-without-error fallback, and no template
  leaks a real home directory instead of the `<you>` placeholder.
- Root `README.md`, `claude/README.md`, and `claude/docs/WORKFLOW.zh-TW.md` link the new
  guide; `CLAUDE.md` records the constraint that `claude/templates/` is copied into someone
  else's home directory and must stay generic.
