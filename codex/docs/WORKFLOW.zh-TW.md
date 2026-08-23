# Agent Advisor for Codex 工作流（Windows-first）

本頁是 SanHsien/agent-advisor fork 的可操作工作流。它補充
[README](../README.md) 的快速開始，集中說明安裝、選路、委派、驗證與維護；
上游歸屬與回顧規則仍見 [FORK.md](../../docs/FORK.md) 和
[UPSTREAM.md](../../docs/UPSTREAM.md)。

## 1. Clone 並確認 fork

維護中的公開 repo 是 SanHsien/agent-advisor；Codex 版的來源上游是
DannyMac180/sol-advisor。在 Windows PowerShell 中 clone 維護中的 repo，
再確認或補上 upstream remote：

~~~
git clone https://github.com/SanHsien/agent-advisor.git
Set-Location .\agent-advisor
git remote add upstream https://github.com/DannyMac180/sol-advisor.git
git remote -v
gh repo set-default SanHsien/agent-advisor
gh repo set-default --view
~~~

`git remote add upstream` 只在 upstream 尚未存在時執行；不要重複新增。預期
origin 指向 `https://github.com/SanHsien/agent-advisor.git`，upstream 指向
`https://github.com/DannyMac180/sol-advisor.git`。所有
push、PR、release 都只指向 SanHsien/agent-advisor。除非使用者在當次對話
明確授權回貢，禁止對 upstream push、開 PR、發 release 或觸發 publish。
建立 PR 時仍明寫 fork owner，並讀取指令輸出的 URL 確認 owner：

~~~
git push origin <branch>
gh pr create --repo SanHsien/agent-advisor --base main --head <branch>
~~~

gh repo set-default 的 repo 是 positional argument；使用
gh repo set-default SanHsien/agent-advisor，不要加不存在的 --repo 旗標。

## 2. 安裝 plugin 與原生角色

### PowerShell（主要路徑）

需要已啟用 plugin 的 Codex CLI 或 ChatGPT desktop app，以及 primary session 的
GPT-5.6 Sol / High。只有選到 delegate 或 full 時才需要 Luna / Max 或
Terra / High 的權限。

~~~
codex plugin marketplace add SanHsien/agent-advisor --ref main
codex plugin add agent-advisor-codex@agent-advisor

$pluginDir = (codex plugin list --json | ConvertFrom-Json).installed |
  Where-Object { $_.pluginId -eq 'agent-advisor-codex@agent-advisor' } |
  Select-Object -First 1 -ExpandProperty source |
  Select-Object -ExpandProperty path

if ([string]::IsNullOrWhiteSpace($pluginDir) -or
    -not (Test-Path -LiteralPath (Join-Path $pluginDir 'scripts/install-agents.ps1') -PathType Leaf)) {
  throw 'Agent Advisor for Codex installer was not found.'
}

$installer = Join-Path $pluginDir 'scripts/install-agents.ps1'
& $installer
& $installer -Check
~~~

安裝器只處理三個精確角色檔，不修改 Codex 設定：

| 原生角色 | 固定 model / effort | 用途 |
| --- | --- | --- |
| agent_advisor_codex_luna_implementer | GPT-5.6 Luna / max | delegate/full 的 bounded 工作 |
| agent_advisor_codex_terra_implementer | GPT-5.6 Terra / high | delegate/full 的判斷密集、高風險或大影響範圍工作 |
| agent_advisor_codex_sol_reviewer | GPT-5.6 Sol / high | 僅 audit/full 的 fresh read-only review |

安裝器是 fail-closed：modified、conflict、unsafe、非 regular file、symlink
或 reparse point 不會被覆寫；明確傳入 null 或空白 -TargetDir 也不會退回
CODEX_HOME。遇到拒絕時，先檢查精準目標，再決定是否由使用者處理，不要
盲目重試或改用另一個角色。

安裝或升級後請關閉並重開，或建立一個 fresh Codex task。全域
AGENTS.md 與已安裝角色是在 task/run 啟動時讀取；既有執行中的 task 不會
可靠地自動重新載入新規則，不能只在同一 task 內繼續等待它生效。

### 暫存 fixture 與 WSL/POSIX 輔助驗證

不要拿真實的 $HOME/.codex/agents 或使用者 role 目錄做測試。PowerShell
用唯一的暫存目錄驗證安裝與選定角色：

~~~
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('agent-advisor-codex-fixture-' + [guid]::NewGuid().ToString('N'))
& codex/plugins/agent-advisor-codex/scripts/install-agents.ps1 -TargetDir $fixture
& codex/plugins/agent-advisor-codex/scripts/install-agents.ps1 -TargetDir $fixture -Check
& codex/plugins/agent-advisor-codex/scripts/install-agents.ps1 -TargetDir $fixture -CheckRole luna -CheckRole sol
~~~

驗證完只處理剛建立且已確認的 fixture 路徑；不要把清理命令指向家目錄、repo
根目錄或未解析的變數。PowerShell gate 也會覆蓋空／null target、conflict、
非 regular destination 與 reparse-point 的拒絕案例。

WSL 或其他 POSIX 環境可在獨立 checkout 執行輔助檢查；Windows gate 仍是主要
路徑：

~~~
fixture="$(mktemp -d)/agents"
bash codex/plugins/agent-advisor-codex/scripts/install-agents.sh --target-dir "$fixture"
bash codex/plugins/agent-advisor-codex/scripts/install-agents.sh --target-dir "$fixture" --check
bash codex/plugins/agent-advisor-codex/scripts/verify.sh
~~~

若 Windows 主機缺少 bash、jq、Python 3.11+（`python3`，`tomllib` 所需）或 rg，tools/dev_check.ps1
會明確略過 POSIX verifier；這不等於 POSIX 已通過，也不取代 PowerShell
驗證。

## 3. 啟動 task 與全域強制路由

全域規則放在 Codex home 的 `AGENTS.md`；Windows 預設通常是
`%USERPROFILE%\.codex\AGENTS.md`，若有設定 `CODEX_HOME` 則以該目錄為準。
修改前先確認實際檔案與是否存在優先權更高的 override：

~~~powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$globalAgents = Join-Path $codexHome 'AGENTS.md'
$globalOverride = Join-Path $codexHome 'AGENTS.override.md'

Get-Item -LiteralPath $globalAgents | Select-Object FullName, Length, LastWriteTime
Test-Path -LiteralPath $globalOverride
~~~

先為既有 `AGENTS.md` 建立可復原備份，再精準加入強制路由段落；不要覆寫原有
跨專案安全、成本與 GitHub 規則。若 `AGENTS.override.md` 存在，必須先讀取並
解決衝突，不能假設 `AGENTS.md` 一定生效。修改後重新讀取新增段落、確認檔案
大小合理並保留備份，然後重開 task 驗證載入結果。

不想在每個新 task 重複確認 primary model／effort 時，在 user-level/global
`AGENTS.md` 放入一行精準的持久聲明：

~~~text
AGENT_ADVISOR_CODEX_PRIMARY_ATTESTATION: gpt-5.6-sol/high
~~~

這是使用者聲明，不是 runtime 驗證。合併後指引中的 marker 只算候選，因為
project `AGENTS.md` 也能仿造文字。先宣告 route，再把 skill 內建
`inspect-primary-attestation.ps1`／`.sh` 當作第一個且唯一允許的 preflight tool
call；它必須只讀確認實際 user-level/global `AGENTS.md` 恰有一筆 marker、是一般
檔案、大小合理，且沒有 user-level `AGENTS.override.md`。通過前不得使用其他工具
或派 agent。觀測到的 metadata 永遠優先：若明確顯示不是
`gpt-5.6-sol/high`，必須停止；若只缺 model、effort 或兩者，通過來源驗證的聲明
只補足缺失欄位，並標記為 operator-attested with verified user-level provenance，
不得在新 task 或 compaction 後再詢問。

在 fresh task 的第一個 task tool call 前，對實質開發工作使用
$agent-advisor-codex:orchestration。實質開發包含建立、修改、除錯、重構、測試、
review、發布與部署程式碼、設定、腳本或 repo 文件。依 observed metadata 優先、
持久聲明只補缺失欄位的順序建立 primary Sol / High 證據，再宣告一次可機器讀取
的 route：

~~~
SELECTIVE ROUTE
mode: solo
risk: contained change; one primary agent can implement and verify it
~~~

宣告以前不要呼叫 task tool；依風險把 mode 改成 delegate、audit 或
full。若 skill 未安裝、未載入，或選定角色的 role/model/effort 證據缺失、
衝突、不可用或不可觀測，必須 fail closed，停止受影響 lane，不得靜默換角色、
換 model、換 reasoning 或繞過路由。

全域規則的邊界如下：

- project 層 [AGENTS.md](../../AGENTS.md) 可以加嚴 repo 限制，但不能關閉、繞過
  或把全域強制路由改成選用。
- 純問答、翻譯、摘要、狀態回報與不涉及開發變更的純唯讀查詢可豁免。
- 更高優先序的 system／developer 指令仍然優先；有衝突時照較高優先序執行
  並說明衝突。
- 全域 AGENTS.md 是 task/run 啟動時載入的規則，不是每個工具呼叫前重新
  讀取；修改全域規則後，重開既有 task 或建立新 task 才能可靠套用。

上游 [issue #25](https://github.com/DannyMac180/sol-advisor/issues/25) 記錄了
每個新 task 重複詢問的問題。本 fork 以 user-level 持久聲明解決，而不是讀取
`config.toml`：default config 不能證明既有 task 的實際 route。若沒有精準聲明、
也沒有 current-task confirmation，缺失欄位仍會停下來詢問一次；精準聲明通過
user-level 檔案來源驗證時不得重複詢問。完整評估記錄在
[UPSTREAM.md](../../docs/UPSTREAM.md)。

建議給 Sol 的起始 prompt：

~~~
Use $agent-advisor-codex:orchestration to build this feature and verify it.
Declare the selective route before task tools.
~~~

## 4. 四種 route 與原生策略

上游原生策略仍保留，Sol 會根據具體風險選路，不能為了形式而重複實作或
review：

| route | 何時使用 | 執行與驗收 |
| --- | --- | --- |
| solo | 預設，風險 contained 且規格不需要獨立審查 | Sol 自己規劃、實作、測試、自我 review；不啟動 auxiliary |
| delegate | 一個完整、明確的工作包適合交給一個 implementer | bounded 工作選 Luna / Max；判斷密集、高風險、context-heavy 或 wide blast radius 選 Terra / High；父代理完整驗證，不另加 fresh reviewer |
| audit | 需要獨立最終 scrutiny，但不需要委派實作 | Sol 自己實作並驗證，之後只啟動 fresh read-only Sol / High reviewer |
| full | 明確的 broad 或 high-risk exception | 一個選定 implementer、父代理驗證，再啟動 fresh read-only Sol / High reviewer |

solo 是預設，通常最多一個 auxiliary；full 是例外。fresh Sol reviewer
只出現在 audit/full。reviewer 回傳 ship、fix-first 或 rethink；
任何修正都會使先前 verdict 失效，父代理重新驗證後必須建立新的 fresh review。

### 委派前的精準 preflight

只檢查當前 route 選到的角色，成功結果只對本次 task 有效。PowerShell 例：

~~~
# delegate / Luna
& $installer -Check -CheckRole luna

# delegate / Terra
& $installer -Check -CheckRole terra

# audit
& $installer -Check -CheckRole sol

# full / Luna 或 Terra + fresh Sol reviewer
& $installer -Check -CheckRole luna -CheckRole sol
& $installer -Check -CheckRole terra -CheckRole sol
~~~

原生 spawn 只指定精準 role 與 fresh context，不附加 model 或 reasoning override：

~~~
agent_type: agent_advisor_codex_luna_implementer
fork_turns: none
~~~

依 route 對應替換為 agent_advisor_codex_terra_implementer 或
agent_advisor_codex_sol_reviewer。public spawn/details metadata 是權威；若只缺
model 或 effort，才可用 skill 提供的 runtime inspector 補那個欄位，不能用它
取代已存在的 public evidence。

## 5. 五段實作工作包（含 RETURN 回報）

委派前由父代理一次解決架構、介面、檔案 ownership 與驗收條件；worker 只執行
完整規格，不重新探索同一問題，也不能擴大 scope。每個工作包至少包含下列
欄位：

~~~
OBJECTIVE
<可觀察的結果，以及它為何重要。>

FILES AND OWNERSHIP
You own only:
- <精準檔案或 module>

You are not alone in the codebase. Preserve concurrent edits, do not revert
unrelated work, and do not modify files outside your ownership.

INTERFACES
- <必須保留的 signature、schema、command 或行為。>

CONSTRAINTS
- <repo 慣例、安全邊界、排除範圍與已決定事項。>

VERIFICATION
- Run: <精準命令>
  Success: <具體預期結果>
- Inspect: <精準檔案、diff 或產物>
  Success: <可觀察證據>

RETURN
Return exact commands and actual evidence. A completion claim without evidence is invalid.
~~~

父代理的 acceptance 不是 worker 的口頭聲明：父代理要檢查完整 working-tree
diff、確認只改 owned files、重新執行驗證，並保留實際輸出。建議要求 worker
用以下格式回報：

~~~
IMPLEMENTATION REPORT
STATUS: complete | partial | blocked
OBJECTIVE: <one-line restatement>
CHANGES: <file-by-file summary from the actual diff>
VERIFIED: <exact commands plus concrete output evidence>
JUDGMENT CALLS: <decisions the specification left open, or none>
GAPS: <unfinished work, ambiguity, or none>
~~~

## 6. 最小驗證與父代理收尾

在 repo root 執行 Windows-first gate，再檢查文件 scope 與 diff：

~~~
pwsh -NoProfile -File tools/dev_check.ps1
git diff --check
git status --short
git diff --stat
git diff -- README.md README.en.md AGENTS.md codex/README.md codex/docs/DEVELOPMENT.md docs/UPSTREAM.md
Get-Content -Raw codex/docs/WORKFLOW.zh-TW.md
~~~

tools/dev_check.ps1 會執行四版的 PowerShell verifier、倉庫層單元測試
（`python -m unittest discover -s tests`）、unstaged/staged git diff --check，
並在工具齊全時執行 POSIX verifier。本機沒有 python 時測試會明確 SKIP，CI 才是測試的權威來源。文件變更完成後，另確認
README、DEVELOPMENT、AGENTS 的連結 target 存在，並檢查新文件中的相對連結：

~~~
$repoRoot = (git rev-parse --show-toplevel).Trim()
@('README.md', 'README.en.md', 'AGENTS.md', 'codex/README.md', 'codex/docs/DEVELOPMENT.md',
  'docs/FORK.md', 'docs/UPSTREAM.md', 'codex/docs/WORKFLOW.zh-TW.md',
  'codex/plugins/agent-advisor-codex/scripts/install-agents.ps1') |
  ForEach-Object {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $_))) {
      throw "Missing documentation target: $_"
    }
  }
~~~

這個檢查以 Git repo root 為基準，只驗證本頁列出的核心 target，不取代完整
diff review。

## 7. 維護與證據紀律

### Marketplace、plugin 與角色升級

升級後重新安裝角色、做全角色 exactness check，並建立 fresh task；不要假設
既有 task 會自動載入新版 skill 或全域規則：

~~~
codex plugin marketplace upgrade agent-advisor
codex plugin add agent-advisor-codex@agent-advisor

$pluginDir = (codex plugin list --json | ConvertFrom-Json).installed |
  Where-Object { $_.pluginId -eq 'agent-advisor-codex@agent-advisor' } |
  Select-Object -First 1 -ExpandProperty source |
  Select-Object -ExpandProperty path
if ([string]::IsNullOrWhiteSpace($pluginDir)) { throw 'Plugin path is empty.' }
$installer = Join-Path $pluginDir 'scripts/install-agents.ps1'
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) { throw 'Installer is missing.' }
& $installer
& $installer -Check
~~~

若只為當前 route 做 preflight，使用 -CheckRole luna、-CheckRole terra 或
-CheckRole sol 的精準組合；缺失、衝突或 unsafe role 必須停止，不可以另一個
角色靜默替代。

### Upstream adopt / skip / defer ledger

先唯讀抓取並列出新 commit，再逐一決定，不把 fork-only Windows／治理變更
直接回灌上游：

~~~
git fetch upstream
git log --oneline --decorate HEAD..upstream/main
git show --stat --oneline <upstream-sha>
~~~

在 [UPSTREAM.md](../../docs/UPSTREAM.md) 記錄 upstream commit 或 release、受影響檔案、
使用的精準驗證命令、adopt／skip／defer 決策與理由。採用後記錄本地
resulting SHA；沒有做決策前不要 merge 或 push。這個 ledger 是維護證據，不是
對 upstream 開 PR 的授權。

### Exact SHA 與 CI

每次回報都把候選內容、CI 與 review 綁在同一個 exact SHA：

~~~
git rev-parse HEAD
git show --check --format= HEAD
gh run view <run-id> --repo SanHsien/agent-advisor --json headSha,status,conclusion,url
~~~

不要只報「CI green」；headSha 必須等於正在驗收的 commit。下列是本次文件
工作開始前、已推送的 fork-tooling baseline，不代表後續未提交文件差異：

- commit：7bd76692bad7ab4d45bc6e35a9c737ae5c60c8cb
- CI：[run 32580873136](https://github.com/SanHsien/agent-advisor/actions/runs/32580873136)，成功

後續教學 candidate 在 commit 前只有本機證據：Windows `DEV CHECK PASSED`、
WSL POSIX `VERIFY PASSED`、文件連結通過，以及 upstream ledger 與 live GitHub
集合一致（7 issues／18 PRs）。這些不能冒充遠端 CI；push 後的最終回報必須
另外核對新 commit SHA 與該 SHA 的 CI run。

本教學最初建立時的 orchestration 證據是：

- 本教學任務宣告 `mode: delegate`：先精準預檢 Luna role，由 Luna / Max 在限定
  文件 ownership 內實作，再由 Sol 檢查完整 diff 並重跑驗證；`delegate` 不另加
  fresh reviewer。
- 初次委派未在時間窗內落檔時，父代理停止無界限等待，對同一 auxiliary 下達
  一次聚焦 correction round；沒有另開第二個 agent 重複探索相同證據。
- review 曾發現並已修正：marketplace 指向錯誤、staged／commit-range diff
  check 遺漏，以及 PowerShell TargetDir 明確 null／empty 時未 fail-closed。

只記錄可公開重現的 SHA、CI URL、命令與結果；不要把 raw session JSON、秘密、
token 或暫存備份路徑寫進 repo 文件。
