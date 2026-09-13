# Agent Advisor for Antigravity 工作流教學

Agent Advisor for Antigravity 把同一套風險分流原則改寫成 Antigravity 原生 plugin bundle：
一個 skill、三個 custom subagent、一條常駐 rule。不會啟動巢狀 CLI，也不會讀取 Codex、
Claude Code 或 Cursor 的設定。

## 安裝

~~~sh
git clone https://github.com/SanHsien/agent-advisor
agy plugin install ./agent-advisor/antigravity/plugins/agent-advisor-antigravity
agy plugin list
~~~

安裝會把整包複製到 `~/.gemini/config/plugins/agent-advisor-antigravity/`。
移除用 `agy plugin uninstall agent-advisor-antigravity`。

## 常駐啟用（本版內建，不必改 GEMINI.md）

`rules/selective-routing.md` 隨 plugin 一起安裝。plugin 啟用時它的 rules 會併進 active
rule set，所以「動工前先宣告路由」就是常駐行為。

**一個實測到的細節**：`agy plugin install` 的元件摘要只列 skills / agents / commands /
mcpServers / hooks，**不列 rules**；`agy plugin list` 對這包也只報
`components: ["skills","agents"]`。但那份摘要不代表全部——安裝器把整包（含 `rules/`）
複製到 `~/.gemini/config/plugins/<name>/`，而 `~/.gemini/config/` 本身就是全域
customization root，rule 從那裡被發現。

真的沒生效時，備援是把
[`templates/AGENTS.md.snippet.md`](../templates/AGENTS.md.snippet.md) 貼進工作區的
`AGENTS.md` 或 `GEMINI.md`。

## 使用

用 pro 級模型、高 effort 開 session：

~~~sh
agy --model gemini-3.1-pro-high --effort high
~~~

Primary 先輸出：

~~~text
SELECTIVE ROUTE
mode: solo | delegate | audit | full
risk: <本任務的精簡風險理由>
~~~

`solo` 是預設；只有工作包完整、委派可真正取代 primary 實作時才使用 `delegate`。
`audit` 適合需要獨立終審的變更；`full` 只用於同時需要委派與獨立 review 的明確高風險例外。

## Antigravity 原生角色

| 角色 | Model tier | 用途 |
| --- | --- | --- |
| `advisor-flash-implementer` | `flash` | 邊界清楚、規格完整的例行實作 |
| `advisor-pro-implementer` | `pro` | 高複雜、高風險或寬影響範圍實作 |
| `advisor-pro-reviewer` | `pro` | `audit`／`full` 的 fresh review |

`model` 收的是 **tier**（`inherit` / `flash` / `pro`），不是帶日期的 model ID——所以模型改版
時 lane 不會跟著壞，這點比 Cursor 版釘死 ID 穩。tier 目前解析到什麼可以用 `agy models` 看。

**effort 跟 tier 是兩件事**：model ID 自帶 effort 後綴，CLI 另有 `--effort low|medium|high`。
不要假設預設值，確認實際生效的那個。

## Hook 的引號陷阱（實測，會癱瘓整個 session）

本 plugin 不帶 hook，但只要你在 Antigravity 裝過 hook 就會踩到：**hook 指令裡的腳本路徑
不能加引號。**

Antigravity 自己把 hook 指令切成 argv，不交給 shell，所以引號會留在檔名裡：

~~~json
"command": "python \"C:\\Users\\<you>\\hooks\\guard.py\""
~~~

Python 直接噴 `[Errno 22] Invalid argument`。而 `PreToolUse` hook 跑在工具之前，
所以**每一個被守的工具呼叫都會失敗**——包含 agent 想拿來修這個檔的那些工具。
Agent 會卡在「要修設定，但修設定需要的工具正好被壞掉的 hook 擋住」。

正確寫法是路徑裸寫：

~~~json
"command": "python C:\\Users\\<you>\\hooks\\guard.py"
~~~

**Claude Code 相反**：它的 hook 指令走 shell，加引號才是對的。這是唯一一條**不能在兩版之間
互抄**的設定。另外，既然沒有 shell 幫忙剝引號，這裡也就無法表達含空白的路徑——hook 腳本
請放在沒有空白的路徑上。

完整範例見 [`templates/hooks-example.json`](../templates/hooks-example.json)。

已經寫壞的檔用附的修復腳本處理。它預設是 dry-run，只印出會改什麼：

~~~sh
python antigravity/scripts/fix_hook_quoting.py
python antigravity/scripts/fix_hook_quoting.py --apply
~~~

腳本會先備份成 `hooks.json.bak-<timestamp>`，然後 parse JSON、對每個 `command` 值套
`^(python|py|python3)\s+"(.+)"$ → \1 \2`、寫回、再重新 `json.load` 確認合法。

**不要用一行 regex 直接改字串。**（例如 `(Get-Content ... -Raw) -replace 'python \\"([^"]+)\\"', 'python $1'`。）
那種寫法沒有備份、不驗證結果、把 JSON 當純文字處理，而這個檔每個路徑都是滿滿的跳脫反斜線——
一個 pattern 沒對準就把整個 hook 設定寫成無法 parse 的檔，症狀比原本的 Errno 22 更難查。

## 驗證與停止條件

Reviewer 用 `commandExecutionPolicy: off` 斷掉 shell 執行。**沒有給 `tools` 白名單是刻意的**：
frontmatter 有這個欄位，但它期待的工具名稱詞彙不在公開的 customization 文件裡，猜一個
識別字的後果是無聲地放寬或清空該 lane 的權限。隔離因此靠執行策略、prompt 合約，
以及 primary 自己比對 review 前後的 `git status --short` 與必要 artifact hash。
若 reviewer 改動任何內容，該 review 無效。

驗證完成、要求的 evidence 已取得就停止，不重複 invoke 第二個 subagent 取得相同證據。
更完整的操作合約見
[operations.md](../plugins/agent-advisor-antigravity/skills/orchestration/references/operations.md)。
