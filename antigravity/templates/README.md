# Templates

Fallback activation for Antigravity. The plugin already ships
`rules/selective-routing.md`, so this is only needed when a session shows no sign of that
rule — or when you want the routing requirement to travel with a repository rather than
with an installed plugin.

| File | Copy to | Purpose |
| --- | --- | --- |
| [`AGENTS.md.snippet.md`](AGENTS.md.snippet.md) | paste into the workspace `AGENTS.md` or `GEMINI.md` | Makes route declaration standing behaviour for that directory tree. |
| [`hooks-example.json`](hooks-example.json) | merge into `~/.gemini/config/hooks.json` or `.agents/hooks.json` | Correctly shaped hook commands. Unrelated to activation — included because the shape is easy to get wrong. |

## The hook quoting trap

Antigravity splits a hook command into argv itself rather than handing it to a shell.
A quoted path therefore keeps its quote characters inside the filename:

~~~json
"command": "python \"C:\\Users\\<you>\\hooks\\guard.py\""
~~~

Python then fails with `[Errno 22] Invalid argument`, and because `PreToolUse` hooks run
*before* the tool does, every guarded tool call fails — including the ones an agent would
need to repair the file. Write the path bare instead:

~~~json
"command": "python C:\\Users\\<you>\\hooks\\guard.py"
~~~

Claude Code runs hook commands through a shell, where the quoted form is correct. This is
the one line you must not copy between the two editions. With no shell to strip quotes
there is also no way to express a path containing spaces, so keep hook scripts on a
space-free path.

**A `PreToolUse` hook must always answer with a `decision`.** The official contract makes
`decision` required. A hook that lets a call through by printing an empty `{}` is read as a
deny with an empty reason (`tool call denied by pre-tool hook: `), so every guarded call is
blocked -- even `python -c "print('hello')"`. Answer `{"decision": "ask"}` to defer to
Antigravity's normal permission flow (it respects "Always Allow"); `"allow"` would
auto-approve and skip the prompt. `PostToolUse` is the event that expects `{}`.

`AGENTS.md` and `GEMINI.md` are directory-scoped: Antigravity walks up from the current
working directory to the repository root and loads every one it finds. They do not
support frontmatter and are always active for their scope.

Background: [`../docs/WORKFLOW.zh-TW.md`](../docs/WORKFLOW.zh-TW.md).
