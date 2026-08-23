[English](README.en.md) | 中文版

# Agent Advisor

> 維護於 [SanHsien/agent-advisor](https://github.com/SanHsien/agent-advisor)。
> Codex 版衍生自 [DannyMac180/sol-advisor](https://github.com/DannyMac180/sol-advisor)，
> 保留原作者署名與 MIT 授權。

Agent Advisor 把同一套風險分流交付流程，包成四個原生 agent runtime 各自的 plugin。
選你這次開發 session 實際在跑的那一版：

| 版本 | 原生角色 | Plugin | 教學 |
| --- | --- | --- | --- |
| Codex | Sol 為 primary；選用 Luna、Terra、Sol reviewer lane | `agent-advisor-codex` | [Agent Advisor for Codex](codex/README.md) |
| Claude Code | Opus 為 primary；選用 Haiku、Sonnet、Opus reviewer lane | `agent-advisor-claude` | [Agent Advisor for Claude Code](claude/README.md) |
| Cursor | 明確指定的高能力模型為 primary；選用 Composer、Sonnet、Opus reviewer lane | `agent-advisor-cursor` | [Agent Advisor for Cursor](cursor/README.md) |
| Antigravity | pro 級為 primary；選用 flash、pro、pro reviewer lane | `agent-advisor-antigravity` | [Agent Advisor for Antigravity](antigravity/README.md) |

每一版都保留四條路由：`solo`、`delegate`、`audit`，以及例外的 `full`。
Primary agent 自己扛架構、路由選擇、驗證與最終驗收。**委派是選擇性的，不是儀式。**

常駐啟用的做法看該 runtime 給不給：Cursor 與 Antigravity 版把常駐規則包在 plugin 裡，
裝好就生效；Claude Code 版沒有這個機制，要改使用者層的 `CLAUDE.md`，
見它的[常駐啟用](claude/README.md#persistent-activation)一節。

## 安裝

### Codex

~~~sh
codex plugin marketplace add SanHsien/agent-advisor --ref main
codex plugin add agent-advisor-codex@agent-advisor
~~~

Codex 版另有原生角色設定檔，需要它自己的安裝器。完整步驟見
[Codex 快速上手](codex/README.md#quick-start)。

### Claude Code

在 Claude Code 內執行：

~~~text
/plugin marketplace add SanHsien/agent-advisor
/plugin install agent-advisor-claude@agent-advisor
~~~

以 Opus 開新 session，然後：

~~~text
Use /agent-advisor-claude:orchestration to declare a SELECTIVE ROUTE before task tools, then build and verify this feature.
~~~

驗證方式與執行期注意事項見 [Claude Code 快速上手](claude/README.md#quick-start)。
要讓宣告路由變成每個 session 的預設行為（而不是每次都要講一遍），見
[常駐啟用](claude/README.md#persistent-activation)。

### Cursor

從側邊欄 **Customize** 面板安裝，或把 Cursor 的本地 plugin 資料夾指到本 repo：

~~~sh
ln -s "$PWD/cursor/plugins/agent-advisor-cursor" ~/.cursor/plugins/local/agent-advisor-cursor
~~~

選一個高能力推理模型——**不要用 `auto`**——就可以開工。內建的 always-apply 規則會自己
要求宣告路由。見 [Cursor 快速上手](cursor/README.md#quick-start)。

### Antigravity

~~~sh
agy plugin install ./antigravity/plugins/agent-advisor-antigravity
agy plugin list
~~~

用 pro 級模型、高 effort 開 session。內建規則會自己要求宣告路由。
見 [Antigravity 快速上手](antigravity/README.md#quick-start)。

**裝 hook 之前先看**：Antigravity 的 hook 指令路徑不能加引號，加了會癱瘓整個 session。
成因與修復見[hook 引號陷阱](antigravity/README.md#the-hook-quoting-trap)。

## 目錄結構

~~~text
codex/        Codex marketplace 來源、plugin、原生角色設定、verifier
claude/       Claude Code marketplace 來源、plugin、Markdown subagents、啟用模板、verifier
cursor/       Cursor plugin、subagents、always-apply 規則、verifier
antigravity/  Antigravity plugin、subagents、always-active 規則、備援模板、verifier
docs/         共用的 fork 與上游維護紀錄
tests/        倉庫層單元測試
tools/        跨平台倉庫 gate
~~~

根目錄的 `.agents/plugins/marketplace.json` 與 `.claude-plugin/marketplace.json` 是 Codex
與 Claude Code CLI 需要的小型探索目錄。所有執行期實作檔都在各自的平台子目錄底下。
Cursor 與 Antigravity 是從 plugin 目錄安裝的，不在根目錄放任何檔案。

## 開發

跑 Windows 優先的倉庫 gate：

~~~powershell
pwsh -NoProfile -File tools/dev_check.ps1
~~~

單獨跑單元測試：

~~~sh
python -m unittest discover -s tests -p "test_*.py"
~~~

各平台文件在 [codex/docs](codex/docs)、[claude/docs](claude/docs)、[cursor/docs](cursor/docs)、
[antigravity/docs](antigravity/docs)。Fork 維護與署名見 [docs/FORK.md](docs/FORK.md)
與 [docs/UPSTREAM.md](docs/UPSTREAM.md)。
