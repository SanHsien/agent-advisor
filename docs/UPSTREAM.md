# Upstream review ledger

Upstream: [DannyMac180/sol-advisor](https://github.com/DannyMac180/sol-advisor)

本 ledger 保存 fork 對上游 issue、PR 與 commit 的逐項判斷，避免下次只看標題
重新評估。外部 contribution 預設只能指向 `SanHsien/agent-advisor`；除非 repo
owner 在當次對話明確授權，不得對 upstream push、開 PR、發 release 或觸發
publish。

## 2026-08-23 review watermark

- Upstream `main`: `37b75cad535abdd46531f0227483a8842d045ab8`
- Fork review base: `7bd76692bad7ab4d45bc6e35a9c737ae5c60c8cb`
- Pre-change immutable comparison:
  `git rev-list --left-right --count 7bd76692bad7ab4d45bc6e35a9c737ae5c60c8cb...37b75cad535abdd46531f0227483a8842d045ab8`:
  `1 0`（當時 fork 多 1 個 Windows/governance commit；upstream 沒有未採用 commit）
- Scope: upstream 全部 7 個 issues 與全部 18 個 PRs，包括 closed/merged/draft。
- Evidence read: issue/PR body、comments、reviews、changed-file list、merge SHA、
  upstream first-parent history、目前 v0.6.0 file set，以及與主張相關的現行
  scripts/contracts。

決策詞義：`adopt` 表示本 fork 已在這次變更採用；`cite` 表示保留為使用者可見
的已知限制；`baseline` 表示已存在於 upstream ancestry，不需另行引用 patch；
`skip` 表示有足夠證據不適用；`defer` 表示問題有效但尚欠明列的驗證條件，
達成 trigger 才重查。

## Issues

| Issue | Decision | Evidence and rationale |
| --- | --- | --- |
| [#1 Runtime inspector null isolation / Python 3.11](https://github.com/DannyMac180/sol-advisor/issues/1) | **adopt docs; defer runtime** | `verify.sh` 現在仍直接 `import tomllib`，README 原本未列 Python 3.11+；已依 #1 與 PR #24 補上。Inspector 仍可能以 exit 0 輸出 null isolation，問題有效；但 reviewer fallback 目前另受 PR #2 的 UUID/path correlation 缺口限制。先不套用舊 v0.4 PR #8；待 v0.6 path/cutoff correlation 可重現後，一併加入 reviewer-only require-isolation 與 absent/malformed fixtures。 |
| [#5 Reviewer verdict vocabulary conflict](https://github.com/DannyMac180/sol-advisor/issues/5) | **skip: superseded** | 現行 v0.6 已移除 commitment-boundary reviewer；只有 `audit/full` final review，唯一 verdict 是 `ship/fix-first/rethink`。`verify.sh` 也拒絕 retired commitment contract，因此原衝突已不存在。 |
| [#7 Unknown `gpt-5.6-luna`](https://github.com/DannyMac180/sol-advisor/issues/7) | **defer: no current reproduction** | 報告引用舊版 Terra/Sol inventory 與 stale routing。v0.6 現在明確 ship Luna/Max、Terra/High、Sol/High 三角色；本次 `-Check -CheckRole luna` 通過且 Luna lane 可啟動。只有在 fresh v0.6 task 再出現 exact unknown-model 錯誤時重查 host routing。 |
| [#11 Independent community guide](https://github.com/DannyMac180/sol-advisor/issues/11) | **skip citation** | 2026-08-23 站點已恢復 HTTP 200，但內容仍描述 pre-v0.6「Terra default / Luna opt-in task」架構，安裝範例也含無效的 nested `sh` invocation，並指向 upstream 而非 maintained fork。連結目前會誤導本 fork 使用者。 |
| [#16 Ambiguous pending Luna task correlation](https://github.com/DannyMac180/sol-advisor/issues/16) | **skip: removed surface** | Issue 指向已移除的 `create_thread`/`clientThreadId` app-task lane 與 `luna-task-lane.md`；v0.6 使用 native fresh-context agent role，repo 內已無這些 symbols/files。 |
| [#20 Windows `PLUGIN_DATA` ACL](https://github.com/DannyMac180/sol-advisor/issues/20) | **skip: removed surface** | v0.6 Codex-only tree 已無 MCP server、`PLUGIN_DATA` 或 persisted adapter state；目前只有 role templates/installers。問題對 v0.5 MCP 有效，但沒有可套用的現行 code path。 |
| [#25 Repeated primary model/effort confirmation](https://github.com/DannyMac180/sol-advisor/issues/25) | **adopt: standing attestation** | 問題適用 v0.6。Fork v0.6.1 接受 user-level/global `AGENTS.md` 的精準 `AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION: gpt-5.6-sol/high`；先宣告 route，再由 bundled first-call inspector 驗證實際 user-level 檔案來源，避免 project 指引仿造。通過後只補足不可觀測的 primary 欄位並避免每個新 task 重問；觀測衝突仍優先且停止。沒有採用 `config.toml` 推斷，因為 default config 不能證明 current task runtime。 |

## Pull requests

| PR | Decision | Evidence and rationale |
| --- | --- | --- |
| [#2 Resolve runtime by spawn path](https://github.com/DannyMac180/sol-advisor/pull/2) | **defer with concrete trigger** | 解決 public spawn handle 沒有 UUID 的方向有價值，但 PR base 是 `d1f390c`、目前 GitHub 狀態 `dirty`/not mergeable，且 diff 綁定 pre-v0.6 contracts。重查條件：先在目前 Desktop 捕捉穩定 `agent_path`、spawn cutoff 與唯一 rollout mapping，再以 v0.6 fixtures 重作；不得直接 cherry-pick。 |
| [#3 Explicit Luna task lane](https://github.com/DannyMac180/sol-advisor/pull/3) | **baseline, superseded** | Merge SHA `52c0f5d...` 已在 upstream ancestry；後續 v0.6 改成 native selective Luna delegate，不再使用舊 user-visible app-task lane。 |
| [#4 Monitored Luna threads / PR graphs](https://github.com/DannyMac180/sol-advisor/pull/4) | **skip** | 要求 Sol/Medium、user-visible task tools 與 layered PR graph，與 v0.6 Sol/High、最多一個 auxiliary、risk-gated route 直接衝突，且修改 retired `luna-task-lane.md`。 |
| [#6 Trim default prompt to 128 chars](https://github.com/DannyMac180/sol-advisor/pull/6) | **baseline** | Merge SHA `154fd7a...` 已在 ancestry。現行 v0.6 兩個 prompts 分別 114/104 chars，仍符合 128-char cap；不需額外 patch。 |
| [#8 Harden reviewer isolation/modes](https://github.com/DannyMac180/sol-advisor/pull/8) | **skip direct; track #1** | PR closed/unmerged，主要 mode fix 對已移除的 commitment review。Isolation 機器化缺口仍有效，已單獨在 issue #1 defer，不能把整個舊架構 patch 引入。 |
| [#9 Verifier assertion and CI](https://github.com/DannyMac180/sol-advisor/pull/9) | **skip direct: fork already covers** | Fork 已有 Windows authoritative gate、Ubuntu POSIX verifier、staged/unstaged/commit-range `diff --check`，且現行 v0.6 manifest verifier 通過。直接套用會重複 Ubuntu gate、夾帶退役 manifest 修正並增加 macOS CI 成本；它不會降低既有 Windows coverage。若 POSIX verifier 出現 macOS-only failure 或 fork 宣告 macOS 為正式 support matrix，再單獨採用 macOS job。 |
| [#10 Reviewer verdict modes](https://github.com/DannyMac180/sol-advisor/pull/10) | **skip: superseded** | 完全針對 issue #5 的 commitment/final dual mode；v0.6 已刪除 commitment mode，套用會重新引入退役契約。 |
| [#12 `projectId` nesting](https://github.com/DannyMac180/sol-advisor/pull/12) | **skip: removed surface** | 只修改已移除的 `create_thread` / `luna-task-lane.md` app-task path；現行 repo 無 `projectId` 或該 schema。 |
| [#13 DeepSeek implementer lane](https://github.com/DannyMac180/sol-advisor/pull/13) | **skip** | 新增第四 role 並移除大量 plugin/MCP/schema surfaces，違反本 fork 的 exact three-role selective contract；同時改變 provider 與 fallback policy，並非相容增量。 |
| [#14 Swedish `Hög` label](https://github.com/DannyMac180/sol-advisor/pull/14) | **skip approach** | Draft 只 hard-code 一個 UI locale。v0.6 應以 canonical runtime effort `high` 為權威；完全不可觀測時明確確認。枚舉 `Hög` 既不能涵蓋其他 locale，也不能證明 current task effort。 |
| [#15 Model-role dashboard](https://github.com/DannyMac180/sol-advisor/pull/15) | **skip** | 870-line local web server、可變 role map 與 regenerated templates 會破壞 shipped exact pins/fail-closed installer，並大幅擴張攻擊面與維護範圍；需求不屬於本 fork。 |
| [#17 Agent Plugin conformance/adapters](https://github.com/DannyMac180/sol-advisor/pull/17) | **historical baseline, reverted** | Merge SHA `ec15017...` 在 ancestry，但 upstream commit `91e2999...` 已 restore Codex-only workflow；現行 v0.6 無 MCP/adapters。不可把已 revert package 當成 current capability。 |
| [#18 Prime Agent package](https://github.com/DannyMac180/sol-advisor/pull/18) | **skip** | 這是獨立 Prime Agent target（數千行 Python、episode store/kernel integration），明確超出 Codex-only fork；沒有現行 plugin interface 可小幅採用。 |
| [#19 v0.5.2 app-task contract](https://github.com/DannyMac180/sol-advisor/pull/19) | **skip: superseded** | Draft 把 user-visible Luna app task 設成 default；upstream 後續 v0.6 已改為 `solo/delegate/audit/full` native selective routes。 |
| [#21 Streamline delivery gates](https://github.com/DannyMac180/sol-advisor/pull/21) | **skip direct: concept superseded** | 單次父驗證、集中 corrections 的成本原則與現行 v0.6 部分一致，但 patch 仍綁定 v0.5 MCP/CHANGELOG/Luna-equivalent flow。現行 contract 已明定各 route review 邊界；直接套用會混合兩套 lifecycle。 |
| [#22 Windows ACL validation](https://github.com/DannyMac180/sol-advisor/pull/22) | **skip: removed surface** | 對 v0.5 MCP 的修正完整且有 Windows 測試，但現行 v0.6 沒有 `server.ts`、MCP state 或 `PLUGIN_DATA`。沒有 target file 可採用；若 upstream 恢復 MCP 才以該版本重新安全審查。 |
| [#23 General Codex router](https://github.com/DannyMac180/sol-advisor/pull/23) | **skip** | 新增 schema-v2 routing entrypoint、usage inspection 與 mutable profiles，改變目前四 route / 三 exact roles 的產品邊界；且是未 rollout 的 draft，不是相容 bugfix。 |
| [#24 Document Python 3.11+](https://github.com/DannyMac180/sol-advisor/pull/24) | **adopt** | PR base 正是 current upstream `37b75c...`，GitHub 顯示 clean/mergeable，主張可由 `verify.sh` 的 `import tomllib` 直接驗證。已在 README、DEVELOPMENT 與繁中 workflow 明列 Python 3.11+，並保留 #24/#1 attribution。 |

## Adopted in this fork review

- 採用 [PR #24](https://github.com/DannyMac180/sol-advisor/pull/24)／
  [issue #1](https://github.com/DannyMac180/sol-advisor/issues/1) 的 Python 3.11+
  maintainer requirement，更新 `README.md`、`docs/DEVELOPMENT.md`、
  `docs/WORKFLOW.zh-TW.md`。
- 採用 [issue #25](https://github.com/DannyMac180/sol-advisor/issues/25) 的問題：
  v0.6.1 新增 user-level 持久聲明，在不把靜態 config 冒充 runtime 證據的前提下
  取消每個新 task 的重複確認。
- 沒有 cherry-pick upstream PR，也沒有對 upstream 進行任何 write action。

## Next review triggers

只在下列事件發生時重查相應項目，不重跑整份 ledger：

1. `upstream/main` 超過 watermark `37b75cad...`：只枚舉新 commits、issues、PRs。
2. Current Desktop 公開穩定的 native agent UUID 或可驗證 `agent_path` + spawn
   cutoff：重查 issue #1 runtime 部分與 PR #2，加入 v0.6 correlation/isolation
   fixtures 後才採用。
3. Host 提供 task-scoped primary model/effort metadata：觀測證據會自動優先；
   驗證新舊 task 與 compaction 行為後，再評估是否能移除 standing attestation。
4. Upstream 恢復 MCP／`PLUGIN_DATA`：才重查 issue #20／PR #22；不能把 v0.5
   ACL patch 直接套在不存在的 surface。

## 分支

上游只有 `main` 一條分支（2026-08-23 確認），沒有其他帶獨佔 commit 的線，所以分支這個面向
沒有可引用的東西。下次要重看分支，觸發條件是：出現相對 `main` 有獨佔 commit、且不屬於任何
open PR 的分支——那才代表有東西被丟在分支上沒走流程。

## 水位怎麼被機器讀

`codex/tools/upstream_baseline.json` 記三個水位，`codex/tools/check_upstream_updates.py`（每週由
`.github/workflows/upstream-check.yml` 執行）只報比水位大的東西。Ticket 查詢
使用 `--state all`，因此在兩次排程之間已關閉或合併的新項目仍會被列出：

| 欄位 | 值 | 意義 |
| --- | --- | --- |
| `reviewed_through` | `37b75ca…` | commit 審到哪 |
| `reviewed_pr_through` | `24` | PR 審到哪 |
| `reviewed_issue_through` | `25` | issue 審到哪 |

`gh` 未授權、API 失敗或回傳不可解析時，check 必須 fail closed，不能把
「未檢查」當成「沒有待審」。處理完新項目後，先把逐項判斷寫進本檔並完成
驗證，再推進對應水位；不能只提高 number 或 commit watermark 讓排程變綠。

## 2026-08-23（第二輪）：上游 PR #26

`37b75ca` 之後上游 `main` 仍是 0 個新 commit，issue 水位未動；新出現的是
[PR #26](https://github.com/DannyMac180/sol-advisor/pull/26)
`Fix primary model detection and add advisory hook`。它有四個可分開判斷的部分，
逐一對照本 fork 的實作：

| 部分 | 本 fork 的現況（實查） | 結論 |
| --- | --- | --- |
| **root rollout 的 `--primary` 檢查**：讓 root session 不必走 subagent-only 的 metadata 路徑 | 本 fork 走的是**另一條路**且更嚴：`inspect-agent-runtime.sh` 只用於 auxiliary（`operations.md` 的用法寫的是 native **subagent** thread id），primary 改由 `inspect-primary-attestation` 驗證 user-level provenance，且 `SKILL.md` 明訂「observed runtime metadata is authoritative；standing attestation 只補**不可觀測**的欄位，且標為 operator-attested 而非 runtime-verified，永不覆蓋觀測到的衝突」。 | **不引用**。上游要解的問題（root 被當 subagent 檢查）在本 fork 的結構下不存在。 |
| **inspector 改讀最新一筆 turn context**，讓 in-thread 換 model 生效 | 本 fork 的 jq 程式收集**所有** `turn_context`，`conflicting models`／`conflicting efforts` 直接 fail。 | **不引用，且這是刻意的**。本 fork 的 inspector 服務對象是 auxiliary：委派期間宣告的 route 必須整段成立，中途換 model 就是證據矛盾，取「最新一筆」等於讓矛盾靜默通過。**觸發條件**：若本 fork 日後把這支 inspector 也用在 primary，就必須改成讀最新一筆，因為使用者本來就能在自己的 thread 裡 `/model`。 |
| **`$…:configure-model-hook` 指令與第二個 skill** | 本 fork 只有 `orchestration` 一個 skill。 | **不引用**：多一個 skill 只為了寫設定檔，成本大於收益；hook 直接隨 plugin 附帶。 |
| **UserPromptSubmit 的 advisory model hook** | 本 fork **沒有**。而 primary 的 model 正是本 fork 唯一只能靠 attestation 的欄位。 | **引用（改寫）**，見下。 |

### 已引用：advisory model hook（改寫成 Python）

上游版是 shell + `jq`。本 fork 是 Windows-first，而**預設 Windows 主機沒有 `jq`**
（本機實測 `jq: command not found`），`python3` 則已經是 `verify.sh` 的既有依賴。因此改寫成
`hooks/observe_primary_model.py`，行為相同、依賴換成本 repo 已經背著的那一個。

三個性質由 `tests/test_observe_primary_model.py` 釘住（13 條）：**永不阻擋**（所有非預期輸入
都 exit 0 且不輸出，host 沒給 `model` 就等於沒安裝）、**永不聲稱 reasoning effort**（hook 拿得到
model 拿不到 effort，含糊帶過會削弱它要強化的那道 gate）、**永不授權 orchestration**。
另外把 model 字串限制在保守字元集後才寫進 developer context——那是別人給的字串。

`verify.sh` 與 `verify.ps1` 都加上必要檔案檢查，兩條路徑不會有一邊漏掉。

### 水位

- PR：**#26**（`reviewed_pr_through` 24 → 26。`--state all` 查過 24 之後的全部 PR，#25 這個編號在上游不是 PR，所以 24 之後只有 #26 一筆）
- issue：仍是 **#25**
- commit：仍是 `37b75ca`（`37b75ca..upstream/main` 為 0）
