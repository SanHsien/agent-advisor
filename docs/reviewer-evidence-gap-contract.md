# Codex reviewer 證據缺口契約（T-20261115-05）

查證日：2026-11-15。只修改 Codex 審查提示；四路由、模型／effort、唯讀設定與三種最終裁決均維持原契約。

## 修改範圍與 diff

原本 [reviewer TOML](../codex/plugins/agent-advisor-codex/agents/agent-advisor-codex-sol-reviewer.toml)
僅要求 evidence-backed findings；[角色契約](../codex/plugins/agent-advisor-codex/skills/orchestration/references/role-contracts.md)
有四個回報欄位與三 verdict，沒有明訂決定性事實未知或既有控制已阻擋時的處理。
兩處加入相同的 `Finding evidence contract` 區塊，直接隨角色及 reviewer prompt 載入。
[契約測試](../tests/test_reviewer_evidence_gap.py) 檢查兩處同步、TOML 可解析、既有介面及下列固定案例。
精確差異可用 `git show --format= -- codex/plugins/agent-advisor-codex/agents/agent-advisor-codex-sol-reviewer.toml codex/plugins/agent-advisor-codex/skills/orchestration/references/role-contracts.md tests/test_reviewer_evidence_gap.py docs/reviewer-evidence-gap-contract.md` 檢視交付 commit。

```text
source-grounded candidate
  +-- reproducible impact ----------> confirmed --------> fix-first / rethink
  +-- decisive fact missing -------> needs_validation --> fix-first / rethink
  +-- evidenced control blocks it --> hardening --------> ship eligible
```

`ship eligible` 仍要求沒有其他必要修正或決定性證據缺口。
finding 狀態只寫在 `FINDINGS`，不新增 verdict 或頂層欄位。
`needs_validation` 必須列已知證據、缺失事實、最小安全驗證與預期觀察；不是收留無來源猜測的狀態。
未驗證的防護不能當作加固建議的降級理由。審查者保持唯讀，由主代理處理必要驗證；缺口需改架構或範圍才可解時用 `rethink`。

## 一手來源與採用界線

2026-11-15 僅網路唯讀查看 Cloudflare 的
[SKILL.md](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/SKILL.md)
與 [VALIDATION-AND-REPORTING.md](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/VALIDATION-AND-REPORTING.md)：
前者要求真實信任邊界與具體影響；後者 Phase 3／4 區分已證實、缺決定性事實與被證據反駁的候選。
Phase 6 已包含 hunter hardening notes；這裡只借鏡證據分級原則，
對應到 advisor verdict 的映射是本 repo 的設計。
未採用其 JSON schema、六階段流程、代理配置或外部程式，未下載執行任何來源內容。
本 repo 的既有格式以角色契約及 orchestration skill 為一手來源；沒有新增執行期 parser。

## 固定案例（合成資料，書面驗收）

以下 `fixture/...` 是描述情境的虛構路徑，非已執行的測試或真實漏洞。四則回報保留既有欄位。

### A：可重現邊界缺陷

```text
SOL REVIEW
VERDICT: fix-first
REASON: 租戶 A 可讀取租戶 B 的合成資料，修正範圍限於查詢授權。
FINDINGS: [confirmed] fixture/read_record.py:8 僅依 record_id 查詢，未限定 tenant_id。重現：假資料 A/1、B/2，以 A 身分查詢 2，回傳 B/2。影響：跨租戶讀取；必要修正：查詢綁定已驗證租戶並補負向案例。
RESIDUAL RISK: 只證明此讀取路徑，不推定可寫入或其他端點也受影響。
```

### B：決定性事實未知

```text
SOL REVIEW
VERDICT: fix-first
REASON: 有來源支撐的候選仍缺決定性證據，尚不能宣稱漏洞或安全通過。
FINDINGS: [needs_validation] fixture/proxy.conf:6 信任 forwarded tenant header，但未知入口是否移除用戶自帶值。缺失事實：入口實際 header 覆寫規則。最小驗證：由主代理以本機假入口及合成租戶送入偽造 header，另核對適用入口設定。預期觀察：移除／覆寫偽造值則否定此路徑；保留且造成跨租戶讀取才可確認影響。未取得入口設定前維持待驗證，不先要求猜測性修碼。
RESIDUAL RISK: 沒有 production 設定證據，不以本機 fixture 推定部署事實。
```

### C：只有防禦縱深建議

```text
SOL REVIEW
VERDICT: ship
REASON: 此情境沒有必要修正或未解決的決定性缺口。
FINDINGS: [hardening] fixture/handler.py:12 可再檢查租戶。阻擋證據：fixture/router.py:5 的必經授權 middleware 已拒絕異租戶，合成負向案例回 403 且未進入 handler；此情境所有入口都經該控制，無可證明影響。選用：handler 再檢查一次以便未來重用；不列必要修正。
RESIDUAL RISK: 若未來新增繞過 middleware 的入口，必須重新評估。
```

### D：未知事實需改範圍才能解

```text
SOL REVIEW
VERDICT: rethink
REASON: 現行範圍只含內部服務，卻要求證明外部入口隔離，需要先修訂驗收邊界。
FINDINGS: [needs_validation] fixture/service.py:4 依賴入口提供租戶身分。缺失事實：由誰保證入口的身分驗證與部署覆蓋。最小驗證：先把入口設定與責任方納入審查範圍，再以合成身分核對完整路徑。預期觀察：取得可核對的入口控制證據，或重設介面以移除該信任假設。
RESIDUAL RISK: 在範圍未調整前，無法判斷整條路徑安全性。
```

## 驗收與證據定位

基準 commit：`331247775c16bc1ab65ba6bf31ba33881cd16bd4`；工作分支 `worker/t05-evidence-gap`。
原交付 commit：`9f7a53c`（`feat(codex-reviewer): separate evidence gaps from defense-in-depth; keep ship/fix-first/rethink (T-20261115-05)`）。
依整合者交接，已在沙盒外執行 `tools/dev_check.ps1`，exit 0；本輪修正 commit 由整合者補記。

原交付驗收紀錄（2026-11-15，Asia/Taipei；非本輪修正後的測試數）：以下串接命令結束碼為 0：

```powershell
python -m py_compile tests/test_reviewer_evidence_gap.py && python -m unittest discover -s tests -p test_reviewer_evidence_gap.py -v && pwsh -NoProfile -File tools/dev_check.ps1
```

結果：focused 3 tests OK；完整 gate 74 tests OK、63 Markdown files checked / 0 broken links、
`DEV CHECK PASSED`。五個平台的 PowerShell／package gate 通過；POSIX verifier 缺 `jq`、`rg`，明確 SKIP，未宣稱通過。
驗證使用既有 gate 的暫存 fixture，未接觸真實使用者 agent 安裝目錄。
`ROADMAP.md` 本輪新增其他平台 reviewer 契約是否同步證據缺口規則的評估，列明理由與驗收方式。

## 複審修正（2026-11-15）

統一 reviewer 首段的 fix-first 為 bounded validation or correction。
[orchestration skill](../codex/plugins/agent-advisor-codex/skills/orchestration/SKILL.md)
及角色契約明訂：只有 needs_validation 的 fix-first 也須由主代理驗證後，
把證據交給新的 fresh reviewer 重新判定，不可自行認定缺口已解而報完成。
若驗證結果需改程式，仍走實作修正、重驗、新 reviewer；僅適用既有 audit/full 路由。
FINDINGS 佔位字加入三個狀態，測試移除重複的模型字串斷言（由 verify.ps1 負責）。

本輪實際 mutation：每次只套用表中變更，執行
`python -m unittest discover -s tests -p "test_reviewer_evidence_gap.py" -v`，
再用 `finally` 還原原始 bytes，並比對確認完整還原。
M2、M3 同時改 TOML 與角色契約，避免只測到兩份文字不同。

| Mutation | 實際改動 | 結果與攔截斷言 |
| --- | --- | --- |
| M2 | 把完整 ship 條件句改成 `ship is allowed even with required corrections and unresolved decisive evidence gaps.` | exit 1；完整 ship 條件句缺失，1 failure |
| M3 | 在證據契約插入 `If every finding is needs_validation, ship.` | exit 1；反向句檢查在兩份來源各失敗，2 failures |
| M4 | TOML 首段改成 `Return exactly one verdict: ship, fix-first, rethink, or needs_validation.` | exit 1；首段三 verdict 句缺失，1 failure |
| 刪 TOML 新段落 | 移除整個 `Finding evidence contract` 區塊，保留合法 TOML 結尾 | exit 1；必要區塊標記缺失，1 failure |

還原後本輪驗收串接命令（exit 0）：

```powershell
python -m unittest discover -s tests -p "test_reviewer_evidence_gap.py" -v && pwsh -NoProfile -File tools/dev_check.ps1
```

focused 5 tests OK；完整 gate 76 tests OK，63 Markdown files checked／0 broken links，
`DEV CHECK PASSED`。Codex、Claude、Cursor、Antigravity PowerShell verifier 與
Hermes package contract 均通過；POSIX 因缺 `jq`、`rg` 明確 SKIP，未宣稱通過。
以上是 `9f7a53c` 上六個檔案的未提交修正驗收；本輪 commit 由整合者補記，未 push 或切分支。

測試是離線契約回歸，能攔下提示區塊漂移、三 verdict／四欄位變動及案例錯誤分類。
它不執行模型，不證明任意 reviewer 都會遵守提示，不宣稱外部來源已通過安全認證。

## 其他平台評估與同步決定（2026-11-20）

依各平台的原生隔離機制與 verdict 格式逐一評估後，結論如下：

| 平台 | 決定 | 原生隔離方式 | Verdict 格式 | 理由與同步內容 |
| --- | --- | --- | --- | --- |
| `claude/` | 採用 | 受限工具白名單（`tools: Read, Glob, Grep, Bash`、`disallowedTools: Agent, Edit, Write`）＋行為唯讀＋父代理前後 `git status --short`／hash 比對（plugin subagent 忽略 `permissionMode`） | `ship`、`fix-first`、`rethink`，接精簡證據條列（無 `SOL REVIEW` 四欄標頭） | 已有專屬 fresh-context reviewer（[advisor-opus-reviewer.md](../claude/plugins/agent-advisor-claude/agents/advisor-opus-reviewer.md)）與三種 verdict；保留原生工具隔離與條列格式，於 reviewer、[role-contracts.md](../claude/plugins/agent-advisor-claude/skills/orchestration/references/role-contracts.md) 與 [SKILL.md](../claude/plugins/agent-advisor-claude/skills/orchestration/SKILL.md) 同步 `Finding evidence contract`（未知阻擋 `ship`、僅 `needs_validation` 的 `fix-first` 驗證後須交由新 fresh reviewer 重判）。 |
| `cursor/` | 採用 | runtime 強制 `readonly: true`＋禁止變更性 shell 指令＋父代理前後 `git status --short`／hash 比對 | `ship`、`fix-first`、`rethink`，接精簡證據條列 | 已有專屬 fresh-context reviewer（[advisor-opus-reviewer.md](../cursor/plugins/agent-advisor-cursor/agents/advisor-opus-reviewer.md)）與三種 verdict；保留 `readonly: true` 與條列格式，於 reviewer、[role-contracts.md](../cursor/plugins/agent-advisor-cursor/skills/orchestration/references/role-contracts.md) 與 [SKILL.md](../cursor/plugins/agent-advisor-cursor/skills/orchestration/SKILL.md) 同步同一證據缺口與驗證後 fresh review 契約。 |
| `antigravity/` | 採用 | `commandExecutionPolicy: off`（停用 shell，刻意不設未公開的 `tools` 欄位）＋行為唯讀＋父代理前後 `git status --short`／hash 比對 | `ship`、`fix-first`、`rethink`，接精簡證據條列 | 已有專屬 fresh-context reviewer（[advisor-pro-reviewer.md](../antigravity/plugins/agent-advisor-antigravity/agents/advisor-pro-reviewer.md)）與三種 verdict；保留 `commandExecutionPolicy: off` 與條列格式，於 reviewer、[role-contracts.md](../antigravity/plugins/agent-advisor-antigravity/skills/orchestration/references/role-contracts.md) 與 [SKILL.md](../antigravity/plugins/agent-advisor-antigravity/skills/orchestration/SKILL.md) 同步同一證據缺口與驗證後 fresh review 契約。 |
| `hermes/` | 採用（原生措辭） | `delegate_task` 無保證的唯讀沙盒，僅靠行為唯讀與父代理前後工作區／hash 檢查 | 無專用 verdict 格式（原生完成與結案判定） | Hermes 在 `audit`／`full` 路線已有 fresh `delegate_task` reviewer。保留原生 skill 結構（不新增獨立角色設定檔、不借用 `ship`／`fix-first`／`rethink` 裁決名），於 [SKILL.md](../hermes/skills/agent-advisor-orchestration/SKILL.md) 採用 Hermes 原生措辭同步證據缺口規則：reviewer 疑點分已證實（`confirmed`）、待驗證（`needs_validation`）、強化建議（`hardening`）三類；有未解決的待驗證即阻擋結案或宣稱通過；驗證後須由新的 fresh reviewer 重審，主代理與原 reviewer 不得自清。 |

跨平台契約測試見 [test_platform_reviewer_evidence_gap.py](../tests/test_platform_reviewer_evidence_gap.py)，檢查採納平台的原生隔離欄位與 verdict 保留、reviewer／packet 契約同步、未知阻擋 `ship` 或完成結案、驗證型缺口不得自清且須再經 fresh review，以及 `hermes/` 以原生措辭落實證據缺口且未混入外部角色或裁決格式。
