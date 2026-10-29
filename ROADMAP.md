# 路線圖

> 本 repo 後續工作的單一真相源。做完一項，就在同一個 commit 刪掉那一列；新工作只加在這裡。
> 現況段的數字是 2026-10-29 依 `main` `7dacc8c1242d` 查的快照，開工前先重查 GitHub。

## 現況
`DannyMac180/sol-advisor` 的衍生版，負責「要不要派工、派給誰」的風險分流路由（`solo`／`delegate`／`audit`／`full`），分 Codex、Claude Code、Cursor、Antigravity 四個版本與 Hermes skill（`AGENTS.md` 的 runtime 分目錄規則）。2026-10-29 查：open PR 0、issue 已停用（未查到 issue 數）、Dependabot 與 code scanning open 0，`main` 上 CI、CodeQL 最近一次 success，Upstream check 最近一次（10-26 05:09 排程）success（2026-10-29 `gh run list -R SanHsien/agent-advisor -b main`）；但上游在那之後開了 PR #33（2026-10-26 14:36，`gh api repos/DannyMac180/sol-advisor/issues/33`），高於 `codex/tools/upstream_baseline.json` 的 PR 水位 32，下次檢查預期轉紅，開工時以 `gh run list -R SanHsien/agent-advisor -w "Upstream check"` 為準。Claude 版的跨 CLI 工人文件仍建議經 agy-staff／agent-relay 把工作交給 `agy`，與維護者 2026-10-27 的 Antigravity 個人訂閱政策衝突；同一份文件也還沒寫出被允許的那條路：寄信給 Antigravity Desktop App，由 App 用自己的登入執行。

## 近期：可以直接動手
| 項目 | 為什麼 | 驗收方式 | 建議執行者 | 證據 |
| --- | --- | --- | --- | --- |
| 改寫跨 CLI 工人的 Antigravity 段：拿掉經 agy-staff 或 `agent_relay send --run agy` 呼叫 `agy` 的建議，改列被允許的派法——`python -m agent_relay send --to antigravity --kind task --project <repo> --ref antigravity-session:new`（Antigravity Desktop 在側邊欄開新對話、用自己的登入執行） | 維護者 2026-10-27 政策：第三方 agent 不得經 `agy -p` 等方式使用 Antigravity 個人訂閱，但派工給 Desktop App 本身視同人下指令；現行文件把 `agy` CLI 列為省額度首選，卻沒寫 Desktop 這條路 | ``grep -rnE "agy-staff\|--run agy" claude/plugins/agent-advisor-claude/skills/orchestration`` 只剩位於政策說明段的行；`cross-cli.md` 的工人表有 Desktop App 那一列、沒有 agy-staff 列；`SKILL.md:83-86` 不再建議直接呼叫 agy；`pwsh -NoProfile -File tools\dev_check.ps1` PASSED；CHANGELOG 中英兩份同步 | Claude Sonnet | `claude/plugins/agent-advisor-claude/skills/orchestration/references/cross-cli.md:7-8`、`:17-18`、`:26`；`claude/plugins/agent-advisor-claude/skills/orchestration/SKILL.md:83-86` |
| 審上游 PR #33「Add minimal GPT-6 family compatibility」，判定 adopt／skip／defer 並推進 PR 水位 | 高於 baseline 的新 PR；內容是 Codex 版的模型清單相容性，可能影響 `codex/` 的 lane 對應 | `docs/UPSTREAM.md` 新增一列附理由；`codex/tools/upstream_baseline.json` 的 `reviewed_pr_through` 推進；`Upstream check` 轉 success | Codex | `gh api repos/DannyMac180/sol-advisor/issues/33`；`codex/tools/upstream_baseline.json` |
| `check_upstream_updates.py` 改用 `-z` 取檔名、baseline 欄位型別錯誤時印明確錯誤而非 traceback | 含空白的檔名會被 `split()` 拆開，報告列出錯的路徑；壞 baseline 直接 traceback | 新 `unittest`：含空白檔名的 commit 報告路徑完整；型別錯誤的 baseline 回非 0 且訊息指出欄位；`python -m unittest discover -s tests` 綠 | Codex | `codex/tools/check_upstream_updates.py:80` |

## 中期：等條件成立再做
| 項目 | 觸發條件 | 驗收方式 | 建議執行者 | 證據 |
| --- | --- | --- | --- | --- |
| 依 `docs/UPSTREAM.md`「Next review triggers」重查對應上游項目（issue #1 runtime 部分、PR #2、issue #20／PR #22 等） | 該節列出的任一條件成立（上游 `main` 超過 watermark、host 提供穩定 agent UUID 或 task-scoped model metadata、上游恢復 MCP／`PLUGIN_DATA`） | 只重查被觸發的項目，結論寫回 `docs/UPSTREAM.md`；採用者附契約測試，dev_check PASSED | Codex | `docs/UPSTREAM.md:86-96` |
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
