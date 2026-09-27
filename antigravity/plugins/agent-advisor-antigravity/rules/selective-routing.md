# Selective routing

Before the first task tool call on any non-trivial task — editing files, multi-file
search, implementation, refactoring, debugging — activate the `orchestration` skill and
emit exactly:

~~~text
SELECTIVE ROUTE
mode: solo | delegate | audit | full
risk: <concise, task-specific rationale>
~~~

Single questions, status lookups, and chat need no declaration.

`solo` is the default. Choose an auxiliary only when a concrete risk or a complete
specification makes one materially useful. A later declaration may escalate after
newly observed risk; it may never silently downgrade.

The primary agent owns intent, architecture, route choice, verification, and final
acceptance — delegation never transfers those.
