# 跨 CLI 工人（Cross-CLI workers）

本檔說明 `delegate` 路由的一個變化：把工作交給**另一個 CLI**（Antigravity `agy`、Codex），而不是 Claude Code 的 plugin subagent。路由仍是四選一，這不是第五條路。

## 什麼時候用

- 機械式、範圍清楚的修改，想省 Claude 額度：交給 `agy`（Gemini Flash）。
- 想要不同模型家族做第二意見：`agy` 的 research／review 模式。
- 工作要在**另一台機器**或另一個 repo 跑，或要排隊等額度：用 agent-relay 寄派工信。

跨 CLI 工人**算作那一個 auxiliary**，預設上限不變。工人的報告仍只是聲明：主 session 照 [cost-policy.md](cost-policy.md) 自己驗證 diff 與測試。

## 兩種呼叫方式

| 方式 | 指令 | 適合 |
| --- | --- | --- |
| 本機技能 | [agy-staff](https://github.com/SanHsien/agy-staff)：`node <agy-staff>/companion/agy-companion.mjs implement --timeout 10m --prompt-file <brief>`，再 `wait <job-id> --timeout 10m` | 同一台機器、同一個 repo，要馬上拿結果 |
| 信件派工 | [agent-relay](https://github.com/SanHsien/agent-relay)：`python -m agent_relay send --kind task --run agy\|codex\|claude --repo <repo> --body-file <brief>` | 跨機器、跨 repo、要留紀錄、可排隊 |

agent-relay 派工會在收件端開 git worktree（分支 `relay/<id>`），指令沿用 [agent-cortex](https://github.com/SanHsien/agent-cortex) launcher 的權限模式，做完自動回 `kind=result` 信。細節見 agent-relay 的 SPEC.md 第 7 節。

## 防呆與逾時

- **一定要給逾時**：agy-staff `--timeout`（最多 120m）；agent-relay `--timeout`（分鐘，最多 120）。超時要結束整棵行程，不能讓主流程卡住。
- **隔離**：交給會改檔的工人前，先開 worktree 或確認工作樹乾淨，事後才看得出它改了什麼。
- **權限**：agy-staff 的 implement／research 預設會帶 `--dangerously-skip-permissions`（agy-staff 的設計）。只在可丟棄的 worktree 裡用；要收緊就加 `--restricted`（需先跑 agy-staff 的 setup）。agent-relay 派 agy 一律 `plan + sandbox`，只讀。
- **brief 照 [role-contracts.md](role-contracts.md)**：OBJECTIVE、FILES AND OWNERSHIP、CONSTRAINTS、VERIFICATION、RETURN。外部 CLI 不認得 plugin agent 的格式，所以要把要求寫進 prompt 本文。

## 回報格式

工人最後一則訊息要有三段：做了什麼、驗證證據（指令與輸出原文）、還沒做的。主 session 收到後：

1. `git -C <worktree> log --oneline <base>..HEAD` 與 `git diff --stat <base>` 看實際變更。
2. 自己重跑 brief 裡的驗證指令。
3. 決定合併、退回重派，或升級到 `audit` 路由。
