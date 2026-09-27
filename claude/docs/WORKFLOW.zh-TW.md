# Agent Advisor for Claude Code 工作流教學

Agent Advisor for Claude Code 把同一套風險分流原則改寫成 Claude Code 原生 plugin。它使用
`SKILL.md` 與 Markdown subagents，不會啟動巢狀 Codex，也不會讀取 Codex 的
`AGENTS.md` attestation。

## 安裝

在 Claude Code 內執行：

~~~text
/plugin marketplace add SanHsien/agent-advisor
/plugin install agent-advisor-claude@agent-advisor
~~~

更新 marketplace 後可使用 `/plugin marketplace update agent-advisor`；若 Claude
Code 顯示需要 reload，依提示執行 `/reload-plugins`，然後以 Opus 開新 session。

`/plugin` 是互動式終端面板，在 desktop app、VS Code、web、SDK 等非 TUI entrypoint
開不了；那些環境的手動安裝步驟見 [ACTIVATION.zh-TW.md](ACTIVATION.zh-TW.md#c-手動安裝非-tui-session)。

## 常駐啟用

裝好只是上架。`orchestration` 和其他 skill 一樣按需喚起——Claude 判斷相關才讀，或使用者
手動打 `/agent-advisor-claude:orchestration`。要讓「動工前先宣告路由」變成每個 session 的
預設行為，把 [`claude/templates/claude-md-snippet.md`](../templates/claude-md-snippet.md)
貼進 `~/.claude/CLAUDE.md`；該檔每個 session 都會自動載入，不需要 hook。

前置條件（Opus model 與 `effortLevel`）、hook 備援、生效範圍，以及三個會讓正確設定看起來
壞掉的陷阱，見 [ACTIVATION.zh-TW.md](ACTIVATION.zh-TW.md)。

## 使用

~~~text
Use /agent-advisor-claude:orchestration to build this feature and verify it. Declare the selective route before task tools.
~~~

Primary 先輸出：

~~~text
SELECTIVE ROUTE
mode: solo | delegate | audit | full
risk: <本任務的精簡風險理由>
~~~

`solo` 是預設；只有工作包完整、委派可真正取代 primary 實作時才使用
`delegate`。`audit` 適合需要獨立終審的變更；`full` 只用於同時需要委派與獨立
review 的明確高風險例外。

## Claude 原生角色

| 角色 | Model alias | 用途 |
| --- | --- | --- |
| `agent-advisor-claude:advisor-haiku-implementer` | `haiku` | 邊界清楚、規格完整的例行實作 |
| `agent-advisor-claude:advisor-sonnet-implementer` | `sonnet` | 高複雜、高風險或寬影響範圍實作 |
| `agent-advisor-claude:advisor-opus-reviewer` | `opus` | `audit`／`full` 的 fresh review |

Claude Code 的組織 allowlist 可能替換 agent frontmatter 要求的 model family。
若 UI 或 agent 啟動訊息顯示替換，受影響 lane 必須停止，不能把不同模型當成
已驗證的路由。

## 驗證與停止條件

Primary 必須自己檢查完整 diff 並重跑驗證。Reviewer 是 plugin subagent，Claude
Code 會忽略 plugin agent 的 `permissionMode`；因此 reviewer 只配置讀取與 shell
查證工具，prompt 禁止 mutation，primary 另比對 review 前後的 `git status --short`
與必要 artifact hash。若 reviewer 改動任何內容，該 review 無效。

驗證完成、要求的 evidence 已取得就停止，不重複 spawn 第二個 agent 取得相同
證據。更完整的操作合約見
[operations.md](../plugins/agent-advisor-claude/skills/orchestration/references/operations.md)。

## Provider 節流／429 恢復

`429 / Too Many Requests` 代表被選中的 Haiku、Sonnet 或 Opus lane 暫時不可用，
不是程式碼失敗，也不會改變原本的風險分級。先保存 checkpoint、worktree、角色、
工作規格、ownership 與剩餘驗證；短暫且有上限的退避後，最多只做一次確認重試。

若再次被節流，停止密集重試，不另開相同 ownership 的平行 agent、不接受 model
substitution，也不讓 primary 重做已委派工作。已要求持續執行且可排程時，才以低頻率
（通常 15–30 分鐘）重試；狀態未變時保持安靜，若 provider 公布 reset time 就以它
為準。恢復前先確認沒有舊 worker 仍在執行，再用原角色、原規格、原 ownership 與
原驗證計畫接續。帳號仍有總用量，不代表特定模型 lane 可用。
