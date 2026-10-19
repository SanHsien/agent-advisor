# 模型混搭改善決策

## 決定

GPT-6.1 Sol／medium 取代 GPT-6 Sol／medium 為 Codex 預設 primary；舊 Sol／medium 保留相容。
輔助 implementer／reviewer 精準配對不變。五版新增成本紀律；Claude 加入原生與 3P profile 合約；Hermes 交付原生 skill。

直接採用短工作包、查核後沿用相同輸入的驗證證據、停止重複查詢與誠實用量記錄。
這些減少不必要工作且保留驗收。原有 repo 強制 gate 與 fresh review 不變。
不採用全面顧問、全面平行或全面降級：已有主模型規劃／便宜模型執行合約，額外角色會增加完整上下文讀取及整合成本。
未做模型比較實驗，不宣稱實測省費百分比，也不新增常駐用量採集工具。

## 各版

- Codex：GPT-6.1 Sol／medium 預設；保留 Luna、Astra 與 legacy Sol 合約。
- Claude：原生 Opus primary；3P 明確選定高能力 primary，分別查核實際解析模型；子角色家族合約不變。
- Cursor：明確選定高能力 primary，不使用 auto；保留原生 readonly reviewer。
- Antigravity：pro／high primary；原生 flash／pro 分工與 commandExecutionPolicy 不變。
- Hermes：沿用選定 provider/model，使用 delegate_task；readonly 為行為約束與工作樹比對，不冒稱 sandbox。

## 來源與限制

- [OpenAI GPT-6.1 Sol](https://openai.com/index/introducing-gpt-6-1-sol/) 與 [model](https://developers.openai.com/api/docs/models/gpt-6.1-sol)：medium 為支援的預設 effort。官方 benchmark 不能直接當本機 workload 結果。
- [Anthropic 成本指南](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence)：比較每件完成工作的成本；混搭不是普遍省費保證。
- [Claude Advisor](https://code.claude.com/docs/en/advisor)：原生顧問有 provider 限制、完整對話讀取與額外費用；不能自動宣稱 3P 可用。
- [Hermes delegation](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation/)：不同 runtime 的 model／provider 解析不可套用另一平台設定。

安裝一致性、設定與檔案存在不是 runtime 驗證。新 session 載入後才可觀察實際執行。
