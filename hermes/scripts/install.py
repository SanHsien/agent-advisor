"""Install only the native Hermes skill; never change provider, plugins, or credentials."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import stat
import time


def is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        return getattr(path.lstat(), 'st_reparse_tag', None) == getattr(stat, 'IO_REPARSE_TAG_MOUNT_POINT', -1)
    except FileNotFoundError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-dir', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--force', action='store_true', help='Back up and replace conflicting skill files')
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / 'skills/agent-advisor-orchestration'
    if 'name: agent-advisor-orchestration' not in (source / 'SKILL.md').read_text(encoding='utf-8'):
        raise SystemExit('Invalid source skill; nothing written')
    raw_home = os.environ.get('HERMES_HOME')
    home = Path(raw_home) if raw_home else (
        Path(os.environ['LOCALAPPDATA']) / 'hermes'
        if os.name == 'nt' and os.environ.get('LOCALAPPDATA') else Path.home() / '.hermes'
    )
    target = args.target_dir or home / 'skills/autonomous-ai-agents/agent-advisor-orchestration'
    target = target.absolute()
    if target == Path(target.anchor) or target == source:
        raise SystemExit('Unsafe target; nothing written')
    for p in (target, *target.parents):
        if p.exists() and (is_link(p) or not p.is_dir()):
            raise SystemExit(f'Unsafe target ancestor: {p}; nothing written')
    files = sorted(p for p in source.rglob('*') if p.is_file())
    changes = []
    for p in files:
        dest = target / p.relative_to(source)
        for ancestor in dest.parents:
            if ancestor == target.parent:
                break
            if is_link(ancestor) or (ancestor.exists() and not ancestor.is_dir()):
                raise SystemExit(f'Unsafe destination ancestor: {ancestor}; nothing written')
        if is_link(dest) or (dest.exists() and not dest.is_file()):
            raise SystemExit(f'Unsafe destination: {dest}; nothing written')
        same = dest.exists() and hashlib.sha256(dest.read_bytes()).digest() == hashlib.sha256(p.read_bytes()).digest()
        if same:
            continue
        if args.check or (dest.exists() and not args.force and not args.dry_run):
            raise SystemExit(f'Not current: {dest}; nothing written; use --dry-run or --force')
        changes.append((p, dest))
    if args.dry_run:
        print(f'DRY RUN: {len(changes)} files would change; nothing written')
        return
    stamp = time.strftime('%Y%m%d-%H%M%S') + f'-{time.time_ns()}'
    backup = target.parent / 'agent-advisor-backups' / stamp
    for p, dest in changes:
        if dest.exists():
            saved = backup / dest.relative_to(target)
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dest, saved)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    print(f'HERMES INSTALL CHECK PASSED: {len(files)} source files; {len(changes)} changed; runtime reload not verified')


if __name__ == '__main__':
    main()
