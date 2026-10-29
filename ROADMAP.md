# 路線圖

> 本 repo 後續工作的單一真相源。做完一項，就在同一個 commit 刪掉那一列；新工作只加在這裡。
> 現況段的數字是 2026-10-29 依 `main` `7dacc8c1242d` 查的快照，開工前先重查 GitHub。

## 現況
`DannyMac180/sol-advisor` 的衍生版，負責「要不要派工、派給誰」的風險分流路由（`solo`／`delegate`／`audit`／`full`），分 Codex、Claude Code、Cursor、Antigravity 四個版本與 Hermes skill（`AGENTS.md` 的 runtime 分目錄規則）。2026-10-29 查：open PR 0、issue 已停用（未查到 issue 數）、Dependabot 與 code scanning open 0，`main` 上 CI、CodeQL 最近一次 success，Upstream check 最近一次（10-26 05:09 排程）success（2026-10-29 `gh run list -R SanHsien/agent-advisor -b main`）；上游 PR #33（2026-10-26 14:36，`gh api repos/DannyMac180/sol-advisor/issues/33`）已於 2026-10-29 審過，裁決 defer（理由與重看條件見 `docs/UPSTREAM.md` 2026-10-29 一節），`codex/tools/upstream_baseline.json` 的 PR 水位已推進到 33；Upstream check 實際狀態以 `gh run list -R SanHsien/agent-advisor -w "Upstream check"` 為準。Claude 版跨 CLI 工人文件已依維護者 2026-10-27 政策改寫，拿掉經 agy-staff 或 `--run agy` 呼叫 `agy` 的建議，改列寄信給 Antigravity Desktop App（由 Desktop 在側邊欄開新對話、用自己的登入執行）。

## 近期：可以直接動手
| 項目 | 為什麼 | 驗收方式 | 建議執行者 | 證據 |
| --- | --- | --- | --- | --- |

## 中期：等條件成立再做
| 項目 | 觸發條件 | 驗收方式 | 建議執行者 | 證據 |
| --- | --- | --- | --- | --- |
| 依 `docs/UPSTREAM.md`「Next review triggers」重查對應上游項目（issue #1 runtime 部分、PR #2、issue #20／PR #22、PR #33 等） | 該節列出的任一條件成立（上游 `main` 超過 watermark、host 提供穩定 agent UUID 或 task-scoped model metadata、上游恢復 MCP／`PLUGIN_DATA`） | 只重查被觸發的項目，結論寫回 `docs/UPSTREAM.md`；採用者附契約測試，dev_check PASSED | Codex | `docs/UPSTREAM.md:94-112` |
| 恢復跨 CLI 交給 Gemini 的建議 | 維護者改用 `GEMINI_API_KEY` 或 Vertex，且 agent-relay／agy-staff 提供不經個人訂閱的呼叫方式 | `cross-cli.md` 指向該正式 API 路徑；dev_check PASSED | Claude Sonnet | `claude/plugins/agent-advisor-claude/skills/orchestration/references/cross-cli.md` |
| `fix_hook_quoting` 處理含空白的引號路徑 | Antigravity 的 hook 指令能以引數陣列或其他方式表達含空白路徑（目前無 shell，無法表達） | 新契約測試涵蓋含空白路徑的 dry-run、備份、冪等、壞輸入拒絕四項；`agy plugin validate` 由維護者實機確認 | Claude Sonnet | `antigravity/scripts/fix_hook_quoting.py`；`AGENTS.md`「修復類腳本」四項規則 |

## 刻意不做
| 不做什麼 | 理由 | 什麼情況下重新考慮 |
| --- | --- | --- |
| 把選擇性路由改成強制派工或強制審查 | 保留上游四條路由語意（`AGENTS.md` 第一條） | 上游改變路由契約 |
| 把 `route-guard` 擴充成通用攔截（危險指令、無證據完成宣稱、紅燈提交） | 那是 harness-guard 的責任（`README.md:125`）；`route-guard` 只檢查路由宣告且刻意 fail-open | harness-guard 停止維護 |
| 在本 repo 實作派工執行（信件、worktree、工人指令組裝） | 執行歸 agent-relay 與 agent-cortex launcher；本 repo 只產出路由決定與 brief 格式 | 不重新考慮 |
| 加套件 manifest、依賴新鮮度檢查或 pytest | 交付物是 shell、TOML 與 Markdown，沒有可比對的依賴宣告（`AGENTS.md`「自動化檢查的範圍」） | 新增需要第三方套件的可執行元件 |

## 維護方式
上游以 commit／PR／issue 三個水位追蹤，`Upstream check` 每週跑，判斷只寫 `docs/UPSTREAM.md`。依賴只有 GitHub Actions，由 Dependabot 開 PR，合併前讀完整 diff。lane 判準改動時，在 CHANGELOG 註明，供 agent-relay 的 `advise` 對照同步。
