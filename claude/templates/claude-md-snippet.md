# CLAUDE.md 常駐路由片段

把下面這段貼進 `~/.claude/CLAUDE.md`（Windows：`%USERPROFILE%\.claude\CLAUDE.md`）。
如果你的 CLAUDE.md 有「開場程序」之類每個 session 必跑的區塊，就放在那裡。

背景與陷阱見 [ACTIVATION.zh-TW.md](../docs/ACTIVATION.zh-TW.md)。

---

**常駐選擇性路由（agent-advisor）**：處理任何非瑣碎任務（要改檔、跨多檔搜尋、實作、重構、
除錯）之前，先 `Skill("agent-advisor-claude:orchestration")`，並在動工前宣告 SELECTIVE ROUTE：
`solo` / `delegate` / `audit` / 例外 `full` 擇一，附一句理由。單一問答、狀態查詢、閒聊不需宣告。
plugin 不在（未重開 session）→ 跳過本步，不報錯。

---

## English

**Persistent selective routing (agent-advisor)**: before any non-trivial task (editing files,
multi-file search, implementation, refactoring, debugging), load
`Skill("agent-advisor-claude:orchestration")` and declare a SELECTIVE ROUTE before starting
work: one of `solo` / `delegate` / `audit` / exceptional `full`, with a one-line reason.
Single questions, status lookups, and chat need no declaration. If the plugin is not loaded
(session not restarted yet), skip this step without raising an error.

## 為什麼是這個位置、這個寫法

- **不要另立一條核心規則。** 常駐路由是每個 session 的例行程序，不是行為紅線。核心規則是最貴的
  常駐 context，能不加就不加。
- **降級行為要寫出來。** 沒有最後那句「跳過本步，不報錯」，還沒重開的 session 每次開場都會噴一個
  找不到 skill 的錯。
- **和既有的委派規則分工講清楚。** 如果你的 CLAUDE.md 已經有「非瑣碎任務派子 agent」之類的規則，
  加一句劃清界線：路由決定「要不要派工」，既有規則決定「派工怎麼寫」。兩者不衝突。
