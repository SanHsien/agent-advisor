# 跨 CLI 工人（Cross-CLI workers）

本檔說明 `delegate` 路由的一個變化：把工作交給**另一個 CLI 或外部 runtime**（Codex、Antigravity Desktop），而不是 Claude Code 的 plugin subagent。路由仍是四選一，這不是第五條路。

## 什麼時候用

- 機械式、範圍清楚的修改，想省 Claude 額度：交給 Codex（例如 GPT-6 Luna／Terra）或 Antigravity Desktop。
- 想要不同模型家族做第二意見：Codex 或 Antigravity Desktop。
- 工作要在**另一台機器**或另一個 repo 跑，或要排隊等額度：用 agent-relay 寄派工信。

跨 CLI 工人**算作那一個 auxiliary**，預設上限不變。工人的報告仍只是聲明：主 session 照 [cost-policy.md](cost-policy.md) 自己驗證 diff 與測試。

## 政策說明（Antigravity 與 agy）

維護者 2026-10-27 政策：第三方 agent 不得經 agy-staff 或 `agent_relay send --run agy`（例如 `agy -p` 等無頭 CLI 方式）使用 Antigravity 個人訂閱；但透過 agent-relay 派工給 Antigravity Desktop App（由 Desktop 在側邊欄開新對話、用自己的登入執行）視同人下指令，為被允許的派法。

## 兩種呼叫方式

| 方式 | 指令 | 適合 |
| --- | --- | --- |
| Antigravity Desktop App | [agent-relay](https://github.com/SanHsien/agent-relay)：`python -m agent_relay send --to antigravity --subject <title> --kind task --project <repo> --ref antigravity-session:new --body-file <brief>` | 本機 Desktop 在側邊欄開新對話、用自己的登入執行 |
| CLI 信件派工 | [agent-relay](https://github.com/SanHsien/agent-relay)：`python -m agent_relay send --kind task --run codex\|claude --repo <repo> --body-file <brief>` | 跨機器、跨 repo、要留紀錄、可排隊 |

agent-relay 派工會在收件端開 git worktree（分支 `relay/<id>`，CLI 工人，做完自動回 `kind=result` 信）或直接在指定 repo 建立新會話（Desktop 工人，sidecar 僅在通知提示用 `--kind result` 回信，不會自動回信）。細節見 agent-relay 的 SPEC.md 第 7 節。

## 防呆與逾時

- **逾時**：agent-relay CLI 派工帶 `--timeout`（分鐘，最多 120），超時要結束整棵行程，不能讓主流程卡住；Desktop 派法沒有 `--timeout`，等待上限由主 session 自己控制。
- **隔離**：交給會改檔的工人前，先開 worktree 或確認工作樹乾淨，事後才看得出它改了什麼。
- **權限**：agent-relay 派工給 CLI 工人會在 worktree 執行；Desktop 在設定的 repo 裡執行，派工前先確認工作樹乾淨。
- **brief 照 [role-contracts.md](role-contracts.md)**：OBJECTIVE、FILES AND OWNERSHIP、CONSTRAINTS、VERIFICATION、RETURN。外部 CLI 不認得 plugin agent 的格式，所以要把要求寫進 prompt 本文。

## 回報格式

工人最後一則訊息要有三段：做了什麼、驗證證據（指令與輸出原文）、還沒做的。主 session 收到後：

1. `git -C <worktree> log --oneline <base>..HEAD` 與 `git diff --stat <base>` 看實際變更。
2. 自己重跑 brief 裡的驗證指令。
3. 決定合併、退回重派，或升級到 `audit` 路由。

## 回流升級（失敗時交給更強的模型）

便宜的跨 CLI 工人沒通過驗收時，不要讓主 session 自己從頭重做，也不要叫同一個工人再試一次：把**真實失敗證據**（驗收指令的輸出結尾、`git diff`）整理好，交給更強的模型在同一個 worktree 診斷並修正，再用同一套驗收重驗。只升級一次；改到範圍外、刪測試、改測試設定這類行為問題不升級，交給人看。

- 經 agent-relay 派工：收件端設 `dispatch.escalation`，relay 會自動做（agent-relay SPEC 第 12 節）。
- 手動做：照 [agent-relay 的回流除錯範本](https://github.com/SanHsien/agent-relay/blob/main/docs/templates/escalation-prompt.md) 寫 prompt，交給 `delegate` 的 deep implementer 或主 session；這仍算那一個 auxiliary。
- 升級後的結果照樣只是聲明：主 session 自己重跑驗證，`audit`／`full` 路由再交 fresh reviewer。
