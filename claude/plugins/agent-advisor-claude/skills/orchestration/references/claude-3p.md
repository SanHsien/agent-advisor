# Claude 原生與 3P

同一套 Claude Code plugin 可以服務原生與 3P session；模型與功能能力必須分別驗證。
不改 gateway、API key、OAuth、模型選單或原生模式偏好，只交付路由與成本合約。
Claude Desktop 3P 是另一個應用設定目錄，不能僅憑 CLI plugin 已安裝就宣稱 Desktop 已載入。

- 原生 profile：Opus primary；既有 Sonnet／Haiku implementer 與 Opus reviewer。
- 3P profile：明確選定高能力 primary。模型由 provider 實際解析；不能依顯示名稱判定。
- 輔助角色仍受既有 family／effort 合約約束。gateway 不支援該角色時停該 lane，保留原 checkpoint；不得冒用名字或靜默換模型。
- Anthropic server-side advisor 預設不開啟；只有 gateway 完整支援且取得可核對證據才選用。顧問不是獨立終審。
- Claude Code 使用實際 CLAUDE_CONFIG_DIR，未設定時用使用者 .claude。不同設定目錄需各自安裝／啟用；Desktop local-agent runtime 使用的目錄需另查證。
- 不宣稱 profile、檔案、安裝一致性是 live runtime 或省費實測。

本機雙模式依既有 Switch-Claude-Mode.ps1：Default 為官方，opencodex 為 3P；空白 Default profile 是正常設計，不可因 profile 空白自行切模式。兩種模式的本機 Code session 使用使用者層 Claude Code plugin。Cowork／Chat 的 Customize 是另一套來源，不以 CLI 安裝冒稱已啟用。

官方模式 UI 的模型選單只證明選單上有哪些名稱，不能證明相同 API model ID、gateway 可用性、價格或輔助 agent 的 runtime。原生維持 Opus family primary 與使用者選定的 effort；不為混搭架構自動改用 Fable 或舊版本。
