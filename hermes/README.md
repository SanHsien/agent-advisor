# Agent Advisor for Hermes

Hermes 原生 skill 使用 `delegate_task`，保留 solo／delegate／audit／full，預設 solo。
不安裝 Claude、Codex 或其他 runtime 的角色設定，不啟動巢狀 CLI。

把 `skills/agent-advisor-orchestration/` 複製到實際 HERMES_HOME 下的
`skills/autonomous-ai-agents/agent-advisor-orchestration/`，包含 references。
安裝前備份同名內容；逐檔 hash 比對後才報告檔案一致。新 session 才可靠載入。
也可用原生安裝器（不改 provider、plugins 或 credentials）：

```powershell
python hermes/scripts/install.py --dry-run
python hermes/scripts/install.py --force
python hermes/scripts/install.py --check
```

`--target-dir` 指定精準 skill 目錄，供不同 profile 或隔離驗證使用。
現有 governance-autoapply adapter 若已啟用，維持原註冊與來源 manifest；檔案安裝不代表 runtime 載入。

主要模型與 provider 由 Hermes 原設定決定；不為省費擅自切換。
輔助模型按 Hermes 的 delegation 設定與實際解析證據確認。
詳見 [skill](skills/agent-advisor-orchestration/SKILL.md)。
