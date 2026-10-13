# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Read-only access to the bare git mirrors (repos/*.git, repos-pro/*.git).

Lets the website show a patched file with surrounding context, expand the full
file at the instance's base_commit, and browse the rest of the repo tree at that
commit — all without a worktree, via `git --git-dir=<mirror> show|ls-tree`.

Every call is read-only (cat-file/ls-tree only) and the path argument is treated
as a git pathspec inside the bare repo, so it cannot touch the host filesystem.
"""
from __future__ import annotations

import functools
import subprocess

from . import data, paths

_GIT_TIMEOUT = 20


def _git(bm: str, instance_id: str, *args: str) -> tuple[int, str]:
    mirror = paths.mirror_for(bm, instance_id)
    if mirror is None:
        return 1, ""
    try:
        p = subprocess.run(
            ["git", "--git-dir", str(mirror), *args],
            capture_output=True, text=True, timeout=_GIT_TIMEOUT,
            errors="replace",
        )
        return p.returncode, p.stdout
    except (subprocess.TimeoutExpired, OSError):
        return 1, ""


def base_commit(bm: str, instance_id: str) -> str | None:
    row = data.dataset_row(bm, instance_id)
    return row.get("base_commit") if row else None


@functools.lru_cache(maxsize=4096)
def file_at_base(bm: str, instance_id: str, path: str) -> str | None:
    """Full content of `path` at the instance's base_commit, or None."""
    bc = base_commit(bm, instance_id)
    if not bc or not path or path.startswith("/") or ".." in path.split("/"):
        return None
    rc, out = _git(bm, instance_id, "show", f"{bc}:{path}")
    return out if rc == 0 else None


@functools.lru_cache(maxsize=1024)
def tree_at_base(bm: str, instance_id: str, subdir: str = "") -> list[dict] | None:
    """One directory level of the repo tree at base_commit.

    Returns [{name, path, type}] where type is 'blob' or 'tree', or None.
    """
    bc = base_commit(bm, instance_id)
    if bc is None:
        return None
    subdir = (subdir or "").strip("/")
    if ".." in subdir.split("/"):
        return None
    spec = f"{bc}:{subdir}" if subdir else bc
    rc, out = _git(bm, instance_id, "ls-tree", "--long", spec)
    if rc != 0:
        return None
    entries = []
    for line in out.splitlines():
        # <mode> <type> <sha> <size>\t<name>
        try:
            meta, name = line.split("\t", 1)
            _mode, typ, _sha, _size = meta.split(None, 3)
        except ValueError:
            continue
        full = f"{subdir}/{name}" if subdir else name
        entries.append({"name": name, "path": full, "type": typ})
    entries.sort(key=lambda e: (e["type"] != "tree", e["name"]))
    return entries


def changed_files(bm: str, bk: str, instance_id: str) -> list[str]:
    """Files touched by the gold patch (from meta.changed_files or the diff)."""
    m = data.meta(bm, bk, instance_id)
    cf = m.get("changed_files")
    if cf:
        return cf
    # fall back to parsing patch.diff target paths
    from . import patchview
    diff = data.read_bundle_file(bm, bk, instance_id, "patch.diff") or ""
    return patchview.changed_paths(diff)
