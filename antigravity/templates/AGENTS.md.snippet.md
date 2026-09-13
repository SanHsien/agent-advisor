# AGENTS.md / GEMINI.md 常駐路由片段

貼進工作區根目錄的 `AGENTS.md` 或 `GEMINI.md`。兩者都不支援 frontmatter，對所在目錄與
其子目錄永遠生效。

---

## Selective routing

Before the first task tool call on any non-trivial task — editing files, multi-file
search, implementation, refactoring, debugging — activate the `orchestration` skill and
emit exactly:

~~~text
SELECTIVE ROUTE
mode: solo | delegate | audit | full
risk: <concise, task-specific rationale>
~~~

Single questions, status lookups, and chat need no declaration.

`solo` is the default. Choose a subagent only when a concrete risk or a complete
specification makes one materially useful. A later declaration may escalate after newly
observed risk; it may never silently downgrade. If the plugin is not installed, skip this
requirement without raising an error.

---

## 為什麼是這個寫法

- **短。** 這段每個 session 常駐，完整合約留在 skill 裡按需載入。
- **降級行為要寫出來。** 沒有最後那句，沒裝 plugin 的工作區每次開場都會噴一個找不到
  skill 的錯。
- **只放在需要的工作區。** `AGENTS.md` 是目錄範圍的；不要為了省事塞進家目錄。
