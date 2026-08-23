[English](CHANGELOG.en.md) | 中文版

# 變更紀錄

格式參考 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，新的在上面。
Codex 版衍生自 [DannyMac180/sol-advisor](https://github.com/DannyMac180/sol-advisor)；
標記 `fork` 的項目是本 fork 相對於該上游的改動。

---

## 2026-08-23（上游 PR #26 與 CodeQL 覆蓋）

### 新增

- **`tools/check_links.py` 與對應的 gate（`fork`）。** 這個 repo 大部分是**互相指來指去的文件**：
  四個 edition 各有 README、docs、plugin skill 與 reference，彼此和根目錄互連，共 49 份 Markdown、
  90 條相對連結。檔案改名或搬家時這些連結會**無聲斷掉**——不會有任何東西報錯，只是下一個讀者
  點過去拿到 404，而不是他被指去讀的那份契約。新檢查只驗相對連結（外部網址交給人看，才能保持
  離線且可重現），以 `git ls-files` 取檔案清單所以本機暫存檔不會讓 gate 變紅。現況實測 49 份、
  0 條斷鏈；注入一條壞連結確認會紅燈。已接進 `dev_check.ps1` 與 CI 兩條路徑。
- **advisory 的 primary model hook（`fork`，取自上游 PR #26 並改寫）。** primary 的 model 是本
  plugin 唯一只能靠 attestation 的欄位——`inspect-agent-runtime` 讀得到 auxiliary 的 rollout，
  primary 的 model／effort 在 session 內部一般不可觀測，所以 gate 只能標成 operator-attested。
  若 host 願意把 active model 交給 hook，這**一個欄位**就能從「被聲明」變成「被觀測」。
  `hooks/observe_primary_model.py` 就只做這麼多：prompt 呼叫 `$agent-advisor-codex:orchestration`
  時印一行 advisory，其餘一律靜默。
  上游版是 shell + `jq`；本 fork 是 Windows-first，而**預設 Windows 主機沒有 `jq`**（本機實測
  `jq: command not found`），`python3` 則已經是 `verify.sh` 的既有依賴，所以改寫成 Python——
  行為相同，依賴換成本 repo 已經背著的那一個。
  三個性質由 `tests/test_observe_primary_model.py`（13 條）釘住：**永不阻擋**（所有非預期輸入
  都 exit 0 且不輸出，host 沒給 `model` 就等於沒安裝，gate 不受影響）、**永不聲稱 reasoning
  effort**（hook 拿得到 model 拿不到 effort，含糊帶過會削弱它要強化的那道 gate）、**永不授權
  orchestration**。model 字串先過保守字元集才寫進 developer context——那是別人給的字串。
  `verify.sh` 與 `verify.ps1` 同步加上必要檔案檢查。

### 變更

- **CodeQL 加掃 `python`（`fork`）。** 原本只掃 `actions`，理由寫的是「這個 repo 沒有應用程式碼
  可以掃」。四種 edition 落地後那個前提不再成立：`antigravity/scripts/fix_hook_quoting.py`
  會**改寫使用者既有的 hooks.json**、`claude/templates/session-start-activation.py` 進使用者的
  session 啟動路徑、`codex/tools/check_upstream_updates.py` 處理外部 API 回應。三者都是「拿別人
  的資料去動別人的檔案」，正是值得掃的形狀。shell 與 PowerShell 仍不在 CodeQL 支援範圍，那部分
  由 verify 腳本與測試守。

### 上游

- **PR #26 四個部分逐一判斷**，只引用其中一個（見 `docs/UPSTREAM.md`）：root rollout 的
  `--primary` 檢查不適用（本 fork 的 inspector 只服務 auxiliary，primary 走 attestation）；
  「改讀最新一筆 turn context」**刻意不引用**——委派期間宣告的 route 必須整段成立，中途換 model
  是證據矛盾，取最新一筆會讓矛盾靜默通過（觸發條件寫在 `docs/UPSTREAM.md`）；
  `configure-model-hook` skill 不引用；advisory hook 引用。`reviewed_pr_through` 推進到 26。

## 2026-08-23（開發環境對齊）

### 新增

- **`tests/`（stdlib `unittest`，無外部依賴）。** 上一輪推了 `fix_hook_quoting.py` 卻沒有測試，
  這是實際缺口。10 個測試釘住這支修復腳本必須守的合約：dry-run 不得寫檔、`--apply` 必須先備份、
  重跑要冪等、JSON 壞掉時拒絕改寫而不是硬寫、非 Python 指令不碰、以及 repo 附的
  `hooks-example.json` 本身必須是「已經正確、無事可修」。
  另外用突變測試證明這些測試真的會抓到回歸：拿掉備份步驟 → 2 個失敗；讓 dry-run 也寫檔 → 1 個失敗。
- **雙語 README 與 CHANGELOG。** 依其他 repo 的慣例，`README.md`／`CHANGELOG.md` 為中文，
  `README.en.md`／`CHANGELOG.en.md` 為英文，兩邊互相有語言切換連結。
- **`NOTICE.md`。** Fork 的署名與授權說明獨立成檔。

### 變更

- `tools/dev_check.ps1` 與 CI 都會跑單元測試。本機沒有 python 時 gate 會明確 SKIP 並說明
  CI 才是測試的權威來源，而不是靜默跳過。

## 2026-08-23（hook 引號）

### 新增

- **Antigravity 的 hook 引號陷阱，已重現並記錄。** Antigravity 自己把 hook 指令切成 argv，
  不交給 shell，所以加了引號的腳本路徑會把引號留在檔名裡，直譯器噴
  `[Errno 22] Invalid argument`。已直接重現：把含引號的檔名丟給 python 就是這個錯，裸路徑則正常。
  Claude Code 的 hook 指令走 shell，加引號才是對的——**這是唯一一條不能在兩版之間互抄的設定**。
- **為什麼比一般設定錯誤嚴重。** `PreToolUse` 跑在工具之前，所以壞掉的 hook 會擋掉每一個被守的
  工具呼叫，包含 agent 想拿來修這個檔的那些。實際觀察到的失敗樣態是 agent 卡住請人手動修設定。
- **[`antigravity/templates/hooks-example.json`](antigravity/templates/hooks-example.json)。**
  正確形狀與內嵌成因，含「沒有 shell 也代表無法表達含空白的路徑」這條限制。
- **[`antigravity/scripts/fix_hook_quoting.py`](antigravity/scripts/fix_hook_quoting.py)。**
  修既有壞檔：預設 dry-run、寫入前先備份、改完重新 parse。它 parse JSON 而不是對原始文字套 regex——
  那個檔每條路徑都是滿滿的跳脫反斜線，pattern 沒對準會留下無法 parse 的設定檔，
  比原本的 `Errno 22` 更難查。

### 變更

- 兩支 Antigravity verifier 各加第 5 道 gate：範例必須維持無引號、以 `python` 呼叫、路徑無空白、
  只用佔位符；修復腳本必須保留 dry-run 預設與備份步驟。
- `claude/templates/settings-example.json` 明確寫出它的引號寫法是**專屬 Claude Code**，
  不得複製到 Antigravity。

## 2026-08-23（Cursor 與 Antigravity 版）

### 新增

- **Cursor 版（`agent-advisor-cursor`）。** Cursor 原生 plugin，含 orchestration skill、
  三個 subagent 與一條 always-apply 規則。Cursor 的 subagent frontmatter 有 `model`、`readonly`、
  `is_background` 但沒有工具白名單，所以 reviewer 的隔離用 `readonly: true`——這是 Cursor 在
  runtime 層強制的，比 Claude Code 版只能靠 prompt 約束更硬。Cursor 沒有穩定的 family alias，
  所以每個 lane 直接釘 model ID，模型不可用時 fail closed。
- **Antigravity 版（`agent-advisor-antigravity`）。** Antigravity 原生 plugin bundle：
  skill、三個 subagent、一條 always-active 規則。subagent 的 `model` 收 tier
  （`inherit`／`flash`／`pro`）而不是帶日期的 ID，所以模型改版時 lane 不會跟著壞。
  已用 Antigravity 自己的檢查器驗過：`agy plugin validate` 回報 1 skill、3 agents processed。
- **兩個新版的常駐啟用都包在 plugin 裡。** 裝好就讓宣告路由變成常駐行為，
  不必動使用者層的設定檔——這點與 Claude Code 版不同。Antigravity 版另附
  `AGENTS.md`／`GEMINI.md` 片段作為備援。
- **一個實測到的安裝器細節，寫下來免得有人再推一次。** `agy plugin install` 的元件摘要會列
  skills、agents、commands、MCP servers、hooks——就是不列 rules；`agy plugin list` 對這包也只報
  `["skills","agents"]`。但摘要不代表全部：安裝器把整包含 `rules/` 複製到
  `~/.gemini/config/plugins/<name>/`，而該目錄本身就是全域 customization root，rule 從那裡被發現。

### 變更

- `tools/dev_check.ps1` 與 `.github/workflows/ci.yml` 跑兩組新的 verifier；POSIX job 現在涵蓋四版。
- 根 `README` 的版本表、安裝章節與目錄結構補上兩個新版。`AGENTS.md` 與 `CLAUDE.md` 記下：
  每一版都要用自己 runtime 真正強制得了的機制表達 lane 隔離，
  且不得輸出該 runtime 沒有公開合法值的 frontmatter 欄位。

### 註記

- Antigravity 的 reviewer 刻意不給 `tools` 白名單。schema 有這個欄位，但它期待的工具名稱詞彙
  沒有公開文件，猜一個識別字會無聲地放寬或清空該 lane 的權限。兩支 verifier 都斷言它保持不存在。

## 2026-08-23（Claude Code 常駐啟用）

### 新增

- **Claude Code 版的常駐啟用。** 裝 plugin 只是上架——`orchestration` 和其他 skill 一樣按需喚起，
  所以宣告路由從來不是 session 的預設行為。新文件
  [`claude/docs/ACTIVATION.zh-TW.md`](claude/docs/ACTIVATION.zh-TW.md) 記錄讓它變成常駐行為的做法，
  在 Windows 11 原生環境實測通過。
- **[`claude/templates/`](claude/templates/README.md) 的可貼上模板。** `CLAUDE.md` 片段
  （主要方法——該檔每個 session 都會自動載入，所以不需要 hook）、釘住 Opus 與 `effortLevel` 的
  `settings.json` 範例，以及一支可選的 `SessionStart` hook（走獨立通道注入，能撐過 context 壓縮）。
  hook 用 Python 不用 shell：Windows 上以裸 `bash` 開頭的 hook 指令會解析到 WSL，
  家目錄不同、腳本不存在，hook 靜默不執行。
- **非 TUI entrypoint 的手動安裝路徑。** `/plugin` 是互動式終端面板，在 desktop app、VS Code、
  web、SDK session 開不了。文件記錄 `/plugin install` 實際做的 JSON 註冊
  （`known_marketplaces.json` 與 `installed_plugins.json`），含那個漏掉就認不出 plugin 的
  隱藏 `.claude-plugin/` 目錄。
- **三個讓正確設定看起來壞掉的陷阱。** 執行中的 session 會把自己的 `effortLevel` 蓋回外部改動；
  launcher 的 `--model` 旗標會無聲蓋過 `settings.json`；`CLAUDE_CODE_EFFORT_LEVEL` 會鎖住整個
  session 讓使用者當場改不了。
- **生效範圍表。** 改動會進到新 session 與 `claude --continue`／`--resume` 的 session，
  但永遠進不到已經在跑的行程：CLAUDE.md、`settings.json`、hooks、plugin 清單都是啟動時快照的。

### 變更

- `claude/scripts/verify.sh` 與 `claude/scripts/verify.ps1` 加了第 4 道 gate 守這些啟用資產：
  檔案存在、settings 範例維持 Opus family 與合法 `effortLevel`、hook 指令用 Python 而非裸 `bash`、
  片段保有四個路由名與「跳過不報錯」的降級句，且沒有模板洩漏真實家目錄。
- 根 `README`、`claude/README.md`、`claude/docs/WORKFLOW.zh-TW.md` 連到新文件；
  `CLAUDE.md` 記下 `claude/templates/` 會被複製到別人的家目錄，必須保持通用。
