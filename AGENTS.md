# Repository guidance

Use Traditional Chinese for user-facing collaboration unless the user asks otherwise.

- Preserve the four upstream routes (`solo`, `delegate`, `audit`, `full`); do not
  silently turn selective routing into mandatory delegation or review.
- Keep changes Windows-first and local-first. PowerShell is the authoritative Windows
  path; POSIX/WSL remains supported.
- Run the narrowest relevant checks. Do not use a real user agent directory or
  credentials in tests: pass a temporary `-TargetDir` or `--target-dir` fixture.
- Keep upstream attribution and the MIT license. Public fork links use
  `SanHsien/agent-advisor`.
- Keep runtime implementations separated: Codex under `codex/`, Claude Code under
  `claude/`, Cursor under `cursor/`, Antigravity under `antigravity/`, with only the
  Codex and Claude Code discovery catalogs at repository root. Cursor and Antigravity
  install from their plugin directory and must not add root files.
- Each edition expresses lane isolation with what its runtime actually enforces, and
  says so in its own docs. Never copy another edition's mechanism as decoration: Claude
  Code uses a restricted tool set, Cursor uses `readonly`, Antigravity uses
  `commandExecutionPolicy`. Do not ship a frontmatter field whose accepted values are
  not documented by that runtime — a guessed identifier fails silently.
- Do not commit, push, create releases, or open pull requests unless explicitly asked.
- Follow the platform workflows in
  [codex/docs/WORKFLOW.zh-TW.md](codex/docs/WORKFLOW.zh-TW.md),
  [claude/docs/WORKFLOW.zh-TW.md](claude/docs/WORKFLOW.zh-TW.md),
  [cursor/docs/WORKFLOW.zh-TW.md](cursor/docs/WORKFLOW.zh-TW.md), and
  [antigravity/docs/WORKFLOW.zh-TW.md](antigravity/docs/WORKFLOW.zh-TW.md); keep this
  file focused on repo-specific constraints and do not weaken any routing contract.

## 維護慣例（全庫一致）

- 一般變更直接推 `origin/main`，不開功能分支、不開維護 PR（維護者 2026-08-22 指示）。
  只有在需要他人審查、或改動風險高到值得先讓 CI 在 PR 上跑一輪時，才退回 branch → PR → CI。
- **合併任何 PR 前必須讀完整 diff**（`gh pr diff <編號>`），包含 Dependabot 開的。CI 綠燈證明的是
  「測試沒紅」，不是「改了什麼、該不該進 main」——action 版本與 workflow 權限的變更只有讀 diff 看得到。
- **PR、push、release 一律指向 `SanHsien/agent-advisor`。** `gh` 在 fork clone 的預設 repo 是上游，
  所以每個 clone 先跑 `gh repo set-default SanHsien/agent-advisor`，開 PR 仍明寫
  `--repo/--base/--head`，並讀輸出的 URL 確認 owner。回貢上游要維護者在當次對話明確同意。

## 自動化檢查的範圍（別再重新推導）

- `ci.yml`：Windows 權威 gate（`tools/dev_check.ps1`）、四個平台的 Ubuntu POSIX verifier，
  以及倉庫層單元測試（stdlib `unittest`，無外部依賴，`tests/`）。
- 測試用 `unittest` 不用 pytest：這個 repo 沒有套件 manifest，也沒打算為了測試多一個依賴。
  新增可執行腳本就要在 `tests/` 補對應的合約測試——修復類腳本尤其要涵蓋 dry-run、備份、
  冪等、壞輸入拒絕改寫這四項。
- `codeql.yml`：只掃 `actions`。這裡沒有 CodeQL 支援的應用程式語言（交付物是 shell 與 TOML），
  真正會出事的是 workflow 本身的注入與權限。
- `upstream-check.yml`：每週比對 Codex 上游的 commit／PR／issue 與 `codex/tools/upstream_baseline.json`
  的三個水位；判斷寫在 [docs/UPSTREAM.md](docs/UPSTREAM.md)，已決定過的項目不會被重新問。
- `dependabot.yml`：**只看 `github-actions`**。這個 repo 沒有套件 manifest，
  因此**也沒有每月依賴新鮮度檢查**——沒有宣告可以拿來跟現行版比對。
