#!/usr/bin/env python3
"""Report upstream work this fork has not reviewed yet: commits, then tickets.

`docs/UPSTREAM.md` records what was decided and why; this answers the narrower
question a schedule needs to ask every week -- has anything new appeared since
that record? It reads three watermarks from `codex/tools/upstream_baseline.json` and
reports only what sits above them, so a decision already written down is never
re-litigated.

Reads only: it fetches upstream into a private ref, never touches `origin`, and
never writes to the upstream repository.

    python codex/tools/check_upstream_updates.py --strict --output upstream-review-report.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = REPO_ROOT / "codex" / "tools" / "upstream_baseline.json"
UPSTREAM_REF = "refs/upstream-check/main"
FULL_SHA_LENGTH = 40
UNIT_SEPARATOR = "\x1f"
REQUIRED_FIELDS = ("repo", "branch", "reviewed_through", "reviewed_date")


class UpstreamCheckError(RuntimeError):
    """Raised when the baseline or upstream history cannot be read."""


def load_baseline(path: Path = BASELINE_PATH) -> dict:
    try:
        baseline = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise UpstreamCheckError(f"cannot read {path}: {error}") from error
    except ValueError as error:
        raise UpstreamCheckError(f"invalid JSON in {path}: {error}") from error
    missing = [field for field in REQUIRED_FIELDS if not baseline.get(field)]
    if missing:
        raise UpstreamCheckError(f"baseline missing fields: {', '.join(missing)}")
    if len(str(baseline["reviewed_through"])) != FULL_SHA_LENGTH:
        raise UpstreamCheckError("reviewed_through must be a full 40-character SHA")
    return baseline


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        raise UpstreamCheckError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def fetch_upstream(baseline: dict) -> None:
    run_git(["fetch", "--quiet", baseline["repo"], f"+refs/heads/{baseline['branch']}:{UPSTREAM_REF}"])


def collect_new_commits(baseline: dict) -> list[dict]:
    raw = run_git(
        [
            "log",
            "--reverse",
            "--date=short",
            f"--format=%H{UNIT_SEPARATOR}%ad{UNIT_SEPARATOR}%s",
            f"{baseline['reviewed_through']}..{UPSTREAM_REF}",
        ]
    )
    commits = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        sha, date, subject = line.split(UNIT_SEPARATOR, 2)
        files = [f for f in run_git(["show", "--name-only", "--format=", sha]).split() if f]
        commits.append({"sha": sha, "short": sha[:7], "date": date, "subject": subject, "files": files})
    return commits


def upstream_slug(repo_url: str) -> str | None:
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<name>[^/]+?)(?:\.git)?$", repo_url)
    return f"{match['owner']}/{match['name']}" if match else None


def collect_new_tickets(baseline: dict, kind: str) -> list[dict] | None:
    """All PRs or issues numbered above the watermark, including closed items.

    Returns ``None`` -- not an empty list -- when ``gh`` cannot answer. ``main``
    treats that state as a fail-closed check error rather than "nothing to review".
    """
    slug = upstream_slug(baseline["repo"])
    if not slug:
        return None
    watermark = int(baseline.get(f"reviewed_{kind}_through", 0) or 0)
    result = subprocess.run(
        ["gh", kind, "list", "--repo", slug, "--state", "all", "--limit", "1000",
         "--json", "number,title"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        return None
    try:
        items = json.loads(result.stdout)
    except ValueError:
        return None
    return sorted(
        (item for item in items if item["number"] > watermark), key=lambda item: item["number"]
    )


def render_ticket_section(title: str, watermark: int, tickets: list[dict] | None, kind: str) -> list[str]:
    lines = [f"## {title}", "", f"Triaged through `#{watermark}`.", ""]
    if tickets is None:
        lines += [
            "Not checked: `gh` was unavailable or unauthenticated. Reported as such rather",
            "than treated as \"nothing to review\" -- the difference matters.",
            "",
        ]
        return lines
    if not tickets:
        lines += ["No new items above that number.", ""]
        return lines
    lines += [f"{len(tickets)} new item(s) to triage.", "", "| Item | Title |", "| --- | --- |"]
    for ticket in tickets:
        lines.append(f"| #{ticket['number']} | {ticket['title'].replace('|', '\\|')} |")
    lines += [
        "",
        f"Record the verdict in `docs/UPSTREAM.md`, then raise `reviewed_{kind}_through`",
        "so the same item is never re-triaged.",
        "",
    ]
    return lines


def render_markdown(baseline: dict, commits: list[dict], prs, issues, error: str | None) -> str:
    lines = [
        "# Upstream review report",
        "",
        f"- Upstream: `{baseline['repo']}` (`{baseline['branch']}`)",
        f"- Reviewed through: `{str(baseline['reviewed_through'])[:7]}`",
        f"- Last review date: {baseline['reviewed_date']}",
        "",
    ]
    if error:
        lines += ["## Check failed", "", "```text", error, "```", ""]
        return "\n".join(lines) + "\n"

    lines += ["## Commits", ""]
    if not commits:
        lines += ["No new upstream commits.", ""]
    else:
        lines += [f"{len(commits)} commit(s) require review.", "", "| Commit | Date | Subject | Files |", "| --- | --- | --- | --- |"]
        for commit in commits:
            files = "<br>".join(commit["files"][:8])
            if len(commit["files"]) > 8:
                files += f"<br>… +{len(commit['files']) - 8} more"
            lines.append(
                f"| `{commit['short']}` | {commit['date']} | {commit['subject'].replace('|', '\\|')} | {files or '(none)'} |"
            )
        lines += ["", "Record adopt/skip decisions in `docs/UPSTREAM.md`, then advance", "`codex/tools/upstream_baseline.json` only after verification.", ""]

    lines += render_ticket_section("Upstream pull requests", int(baseline.get("reviewed_pr_through", 0) or 0), prs, "pr")
    lines += render_ticket_section("Upstream issues", int(baseline.get("reviewed_issue_through", 0) or 0), issues, "issue")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="upstream-review-report.md")
    parser.add_argument("--github-output", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    baseline: dict = {"repo": "unknown", "branch": "unknown", "reviewed_through": "0" * 40, "reviewed_date": "unknown"}
    commits: list[dict] = []
    prs = issues = None
    error: str | None = None
    try:
        baseline = load_baseline()
        fetch_upstream(baseline)
        commits = collect_new_commits(baseline)
        prs = collect_new_tickets(baseline, "pr")
        issues = collect_new_tickets(baseline, "issue")
        unavailable = [name for name, result in (("PRs", prs), ("issues", issues)) if result is None]
        if unavailable:
            raise UpstreamCheckError(
                "gh could not enumerate upstream " + " and ".join(unavailable)
            )
    except UpstreamCheckError as caught:
        error = str(caught)

    report = render_markdown(baseline, commits, prs, issues, error)
    Path(args.output).write_text(report, encoding="utf-8")
    print(report)

    pending = len(commits) + len(prs or []) + len(issues or [])
    if args.github_output and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write(f"needs_attention={'true' if pending or error else 'false'}\n")
            handle.write(f"check_failed={'true' if error else 'false'}\n")
            handle.write(f"report_path={args.output}\n")

    if error:
        return 2
    return 1 if args.strict and pending else 0


if __name__ == "__main__":
    raise SystemExit(main())
