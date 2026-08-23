# NOTICE

agent-advisor (SanHsien maintenance fork)
Copyright 2026 SanHsien

This project is derived from
[`DannyMac180/sol-advisor`](https://github.com/DannyMac180/sol-advisor), originally
licensed under the MIT License.

Original work:

- Project: `sol-advisor`
- Author: Daniel McAteer (`DannyMac180`)
- License: MIT
- Original copyright notice: `Copyright (c) 2026 Daniel McAteer`

The original MIT license text is kept verbatim in [`LICENSE`](LICENSE), and the same file
ships inside every plugin directory so the notice travels with an installed plugin.

## What came from upstream and what did not

The `codex/` edition is the direct descendant of the upstream project: its four routes
(`solo`, `delegate`, `audit`, `full`), the selective-routing principle, and the role
contracts originate there. Upstream review decisions are tracked in
[`docs/UPSTREAM.md`](docs/UPSTREAM.md) and [`docs/FORK.md`](docs/FORK.md).

The `claude/`, `cursor/`, and `antigravity/` editions are new work in this fork. They
carry the same routing design across to other agent runtimes, but their skills,
subagents, rules, templates, and verifiers were written here and have no upstream
counterpart.

## License notes

The MIT License permits use, copying, modification, merging, publication, distribution,
sublicensing, and commercial use, provided the original copyright notice and permission
notice are included in all copies or substantial portions of the software. Keep this
file and `LICENSE` attached when redistributing any part of this repository.

Modifications, documentation, and project-specific changes in this fork are maintained by
SanHsien unless otherwise noted.
