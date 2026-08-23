# Agent Advisor for Cursor 工作流教學

Agent Advisor for Cursor 把同一套風險分流原則改寫成 Cursor 原生 plugin。它使用
`SKILL.md`、Markdown subagents 與 `.mdc` 規則，不會啟動巢狀 CLI，也不會讀取 Codex 或
Claude Code 的設定。

## 安裝

側邊欄 **Customize** 面板找到 plugin → **Install** → 選 project 或 user scope。

不透過 marketplace 時，把 plugin 目錄放進 Cursor 的本地 plugin 資料夾（複製或 symlink 都可）：

~~~powershell
$dst = "$env:USERPROFILE\.cursor\plugins\local\agent-advisor-cursor"
New-Item -ItemType SymbolicLink -Path $dst -Target (Resolve-Path .\cursor\plugins\agent-advisor-cursor)
~~~

## 常駐啟用（本版內建，不必改設定檔）

`rules/selective-routing.mdc` 的 `alwaysApply: true` 隨 plugin 一起安裝，所以裝好、啟用、
重開 session 之後，「動工前先宣告路由」就是每個 session 的預設行為——不需要像 Claude Code
版那樣去改使用者層的 `CLAUDE.md`。

分工是刻意的：**規則**只放「要宣告、預設 solo」這條要求（每個 session 常駐，所以要短）；
**skill** 放完整合約（按需載入，可以長）。

## 使用

選一個高能力推理模型，**不要用 `auto`**——它可能在 session 中途解析到快速模型，
architect 角色依賴的推理就這樣無聲消失了。

規則會自己要求宣告，所以不點名 skill 也可以；要明講就用：

~~~text
Use the orchestration skill to build this feature and verify it. Declare the selective route before task tools.
~~~

Primary 先輸出：

~~~text
SELECTIVE ROUTE
mode: solo | delegate | audit | full
risk: <本任務的精簡風險理由>
~~~

`solo` 是預設；只有工作包完整、委派可真正取代 primary 實作時才使用 `delegate`。
`audit` 適合需要獨立終審的變更；`full` 只用於同時需要委派與獨立 review 的明確高風險例外。

## Cursor 原生角色

| 角色 | Model | 用途 |
| --- | --- | --- |
| `advisor-composer-implementer` | `composer-2.5` | 邊界清楚、規格完整的例行實作 |
| `advisor-sonnet-implementer` | `claude-sonnet-5-thinking-high` | 高複雜、高風險或寬影響範圍實作 |
| `advisor-opus-reviewer` | `claude-opus-5-thinking-high` | `audit`／`full` 的 fresh review |

Cursor 沒有穩定的 model family alias，所以每個 lane 直接釘 model ID。改動前先用
`cursor-agent models` 對一次現行清單。釘死的 ID 是**故意 fail closed**：目前方案跑不了
那個模型時該 lane 停掉，而不是讓 Cursor 換一個模型繼續跑。

## 驗證與停止條件

Reviewer 的 `readonly: true` 由 Cursor 在 runtime 層強制，這比只靠 prompt 約束可靠；
但 primary 仍要自己檢查完整 diff 並重跑驗證，並比對 review 前後的 `git status --short`
與必要 artifact hash。若 reviewer 改動任何內容，該 review 無效。

驗證完成、要求的 evidence 已取得就停止，不重複 spawn 第二個 agent 取得相同證據。
更完整的操作合約見
[operations.md](../plugins/agent-advisor-cursor/skills/orchestration/references/operations.md)。
