# 常駐啟用指南（Claude Code）

`/plugin install` 只把 plugin 放上架，**不會讓它自動生效**。`orchestration` skill 和其他
skill 一樣是按需喚起的：Claude 判斷任務相關才讀，或使用者手動打 `/agent-advisor-claude:orchestration`。

想讓「動工前先宣告 SELECTIVE ROUTE」變成每個 session 的預設行為，需要額外接線。本文記錄
在 Windows 11 原生環境實測通過的做法，以及三個會讓人以為設定失敗的陷阱。

- 前置條件：[模型與 reasoning effort](#模型與-reasoning-effort)
- 主要方法：[A. 寫進使用者 CLAUDE.md](#a-寫進使用者-claudemd主要方法)
- 備援：[B. SessionStart hook 注入](#b-sessionstart-hook-注入備援)
- 面板開不了時：[C. 手動安裝](#c-手動安裝非-tui-session)
- 界線：[哪些 session 吃得到](#哪些-session-吃得到)

## 模型與 reasoning effort

`SKILL.md` 要求 primary session 跑在 Opus family，否則停止實質工作。把它設成全域預設：

~~~json
{
  "model": "claude-opus-5",
  "effortLevel": "high"
}
~~~

寫進 `~/.claude/settings.json`（Windows：`%USERPROFILE%\.claude\settings.json`）。
完整範例見 [`claude/templates/settings-example.json`](../templates/settings-example.json)。

| 項目 | 值 |
| --- | --- |
| settings 鍵名 | `effortLevel` |
| 合法值 | `low`、`medium`、`high`、`xhigh`、`max` |
| 互動指令 | `/effort <level>`（會寫回 settings.json） |
| 環境變數 | `CLAUDE_CODE_EFFORT_LEVEL` |

用完整 model id（`claude-opus-5`）比用 alias（`opus`）明確：alias 會被 launcher 旗標蓋掉，
見陷阱 2。

### 陷阱 1：執行中的 session 會把 effortLevel 蓋回去

從外部改 `effortLevel` 之後，**正在跑的 session 偵測到檔案變動，會把它自己當下的 effort
寫回設定檔**。實測寫入 `high` 後立刻被改回 `medium`。

對策：改完立刻複查；或乾脆在新 session 裡打一次 `/effort high`，讓 CLI 自己寫，就不會被自己蓋掉。

### 陷阱 2：launcher 的 `--model` 旗標蓋過 settings.json

如果用包裝腳本啟動（例如為了固定 `--channels`），裡面寫死的 `--model` 會讓 `settings.json`
的 `model` 完全失效：

~~~bat
@echo off
rem 錯誤：--model 蓋掉 settings.json，怎麼改設定都沒用
claude.exe --model claude-opus-4-8 --channels "plugin:telegram@..." %*
~~~

拿掉 `--model`，讓 `settings.json` 當單一來源：

~~~bat
@echo off
claude.exe --channels "plugin:telegram@..." %*
~~~

### 陷阱 3：`CLAUDE_CODE_EFFORT_LEVEL` 不適合做永久設定

設了會鎖住整個 session，CLI 會顯示 `Not applied: CLAUDE_CODE_EFFORT_LEVEL=... overrides
effort this session`，使用者當場改不了。永久設定請用 `settings.json`。

## A. 寫進使用者 CLAUDE.md（主要方法）

`~/.claude/CLAUDE.md` 每個 session 啟動時自動載入 model context，**這本身就是常駐機制，
不需要額外 hook**。把 [`claude/templates/claude-md-snippet.md`](../templates/claude-md-snippet.md)
的內容貼進去即可。

放置位置建議：如果你的 CLAUDE.md 有「開場程序」之類每個 session 必跑的區塊，就放那裡；
沒有的話放在檔案靠前的位置。

兩個實務判斷：

- **不要為它新增一條核心規則。** 常駐路由屬於「每個 session 的例行程序」，不是行為紅線。
  塞進核心規則會撐大最貴的那段常駐 context。
- **明確寫出降級行為。** plugin 沒載入（例如還沒重開 session）時要跳過而不是報錯，
  否則舊 session 每次開場都會噴一個找不到 skill 的錯誤。

## B. SessionStart hook 注入（備援）

方法 A 已足夠。加這層的理由只有一個：CLAUDE.md 在長對話被壓縮後可能失去強制力，而
`SessionStart` hook 的 `additionalContext` 是直接注入 model context 的獨立通道。

範例見 [`claude/templates/session-start-activation.py`](../templates/session-start-activation.py)，
接線方式見 [`claude/templates/settings-example.json`](../templates/settings-example.json)。

Windows 上 hook 一律用 Python，不要寫裸 `bash`：`bash` 在 Windows 會解析到
`C:\Windows\System32\bash.exe`（也就是 WSL），家目錄不同，`~/.claude/hooks/x.sh` 在那邊
不存在，hook 會靜默失效。Python 沒有這個歧義，也不需要 `jq`。

## C. 手動安裝（非 TUI session）

`/plugin` 是互動式終端面板，在 desktop app、VS Code、web、SDK 等非 TUI entrypoint 開不了。
這時可以手動完成 `/plugin install` 會做的事——以下步驟在 Windows 11 實測通過。

以 `<mp>` = marketplace 名稱（本 repo 是 `agent-advisor`）、`<plugin>` = `agent-advisor-claude`：

1. Clone 到 `~/.claude/plugins/marketplaces/<mp>/`
2. 複製 plugin 目錄到 `~/.claude/plugins/cache/<mp>/<plugin>/<version>/`
   （**要含隱藏的 `.claude-plugin/`**，漏了 Claude Code 認不出這是 plugin）
3. `~/.claude/plugins/known_marketplaces.json` 加一筆：

   ~~~json
   {
     "agent-advisor": {
       "source": { "source": "github", "repo": "SanHsien/agent-advisor" },
       "installLocation": "C:\Users\<you>\.claude\plugins\marketplaces\agent-advisor",
       "lastUpdated": "2026-08-23T00:00:00.000Z"
     }
   }
   ~~~

4. `~/.claude/plugins/installed_plugins.json` 的 `plugins` 加 key `"<plugin>@<mp>"`，
   值是**陣列**：

   ~~~json
   {
     "agent-advisor-claude@agent-advisor": [
       {
         "scope": "user",
         "installPath": "C:\Users\<you>\.claude\plugins\cache\agent-advisor\agent-advisor-claude\1.0.0",
         "version": "1.0.0",
         "installedAt": "2026-08-23T00:00:00.000Z",
         "lastUpdated": "2026-08-23T00:00:00.000Z",
         "gitCommitSha": "<commit>"
       }
     ]
   }
   ~~~

5. 兩個 JSON 先備份（同目錄 `.bak-<timestamp>`）
6. 重開 session，然後跑 `sh claude/scripts/verify.sh` 確認 plugin 內容完整（exit 0）

## 哪些 session 吃得到

| session 類型 | 自動套用 |
| --- | --- |
| 重開後的新 session | ✅ |
| `claude --continue` / `--resume` 接續舊對話 | ✅（新行程，會重讀 CLAUDE.md 與 plugin） |
| 此刻正開著的視窗 | ❌ |

正在跑的行程在啟動時就把 CLAUDE.md、`settings.json`、hooks、plugin 清單全部快照進 context，
中途不重讀——hook 尤其是刻意設計成啟動時鎖定，避免被中途竄改。

所以「舊 session 也要生效」的正確做法不是想辦法熱更新，而是 `claude --continue`：
對話歷史留著，行程是新的，設定與 plugin 都會重新載入。
