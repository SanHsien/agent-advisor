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
這裡只借鏡證據分級原則；`hardening` 及其對 advisor verdict 的映射是本 repo 的設計。
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
本輪尚無交付 commit：沙盒拒絕建立 `.git/index.lock`（Permission denied），改動留在工作樹。
整合者提交後可用 `git log -1 --format=fuller -- docs/reviewer-evidence-gap-contract.md` 定位，避免自引尚未生成的 hash。

2026-11-15（Asia/Taipei）實際執行，以下串接命令結束碼為 0：

```powershell
python -m py_compile tests/test_reviewer_evidence_gap.py && python -m unittest discover -s tests -p test_reviewer_evidence_gap.py -v && pwsh -NoProfile -File tools/dev_check.ps1
```

結果：focused 3 tests OK；完整 gate 74 tests OK、63 Markdown files checked / 0 broken links、
`DEV CHECK PASSED`。五個平台的 PowerShell／package gate 通過；POSIX verifier 缺 `jq`、`rg`，明確 SKIP，未宣稱通過。
驗證使用既有 gate 的暫存 fixture，未接觸真實使用者 agent 安裝目錄。
`ROADMAP.md` 已核對，沒有本任務的待辦列可刪，也沒有新增待辦。

本機提交嘗試（前置連結與 diff 檢查成功；`git add` 拒絕建立 index.lock，整段命令結束碼 1，`git commit` 未執行）：

```powershell
python tools/check_links.py > $null && git diff --check && git add -- codex/plugins/agent-advisor-codex/agents/agent-advisor-codex-sol-reviewer.toml codex/plugins/agent-advisor-codex/skills/orchestration/references/role-contracts.md tests/test_reviewer_evidence_gap.py docs/reviewer-evidence-gap-contract.md && git commit -m 'fix(codex): distinguish reviewer evidence gaps from hardening' -m 'Co-Authored-By: GPT-6.1 Sol <noreply@openai.com>'
```

STATUS: PARTIAL：契約、固定案例、測試與文件完成；缺交付 commit 綁定。未 push、切分支或修改其他安裝。

測試是離線契約回歸，能攔下提示區塊漂移、三 verdict／四欄位變動及案例錯誤分類。
它不執行模型，不證明任意 reviewer 都會遵守提示，不宣稱外部來源已通過安全認證。
