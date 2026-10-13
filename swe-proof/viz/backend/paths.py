# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Canonical filesystem locations + path-traversal guards (read-only).

Unified split layout: <bench root>/<instance_id>/ holds the immutable inputs
(instance.json, patch.diff); the constructed bundle for the reviewed backend
lives in <bench root>/<instance_id>/<backend>/. Every file/blob the website
serves is resolved through `safe_under()` so a crafted instance_id or path can
never escape the dataset roots.

The bench/mirror roots are per BENCHMARK (verified | pro) — every accessor takes
the benchmark key as its first argument, so no module-level state decides which
dataset a request reads.
"""
from __future__ import annotations

from pathlib import Path

from . import settings

# repo root = three levels up from this file (viz/backend/paths.py -> repo/)
REPO_ROOT = Path(__file__).resolve().parents[2]

VIZ_DATA = REPO_ROOT / "viz" / "data"
VIZ_DATA.mkdir(parents=True, exist_ok=True)
# one shared comments DB; rows carry (benchmark, backend) columns
REVIEW_DB = VIZ_DATA / "review.sqlite"


def bench_root(bm: str) -> Path:
    """Bundle root for a benchmark (benchmark-verified/ or benchmark-pro/)."""
    return REPO_ROOT / settings.benchmark_dir(bm)


def repos_root(bm: str) -> Path:
    """Bare-mirror root for a benchmark (repos/ or repos-pro/)."""
    return REPO_ROOT / settings.benchmark_repos(bm)


def bundle_dir(bm: str, bk: str, instance_id: str) -> Path:
    """The backend bundle dir (model.py / Solution.lean, meta.json, ...)."""
    return bench_root(bm) / instance_id / bk


def instance_dir(bm: str, instance_id: str) -> Path:
    """The instance-level dir (instance.json, patch.diff)."""
    return bench_root(bm) / instance_id


def mirror_for(bm: str, instance_id: str) -> Path | None:
    """Resolve the bare clone holding this instance's history.

    Pro ids look like instance_<org>__<proj>-<sha>-v<sha> and the clone under
    repos-pro/ is <org>_<proj>.git; Verified ids look like <org>__<proj>-<num>
    and the clone under repos/ is <org>_<proj>.git. Both reduce to "the segment
    before the first '-', with __ -> _".

    ALWAYS returns a git DIRECTORY (bare repo or a worktree's .git), because
    callers pass it to `git --git-dir` — never a worktree root.
    """
    if not instance_id or "/" in instance_id or "\\" in instance_id or ".." in instance_id:
        return None
    stem = instance_id
    if stem.startswith("instance_"):
        stem = stem[len("instance_"):]
    org_proj = stem.split("-")[0].replace("__", "_")
    root = repos_root(bm)
    mirror = root / (org_proj + ".git")
    if mirror.is_dir():
        return mirror
    # a non-bare clone: hand back its gitdir, not the worktree root
    gitdir = root / org_proj / ".git"
    return gitdir if gitdir.is_dir() else None


def safe_under(root: Path, *parts: str) -> Path:
    """Resolve root/parts and assert the result stays inside root.

    Rejects absolute parts, '..' escapes, and symlink escapes. Raises
    ValueError on any attempt to leave `root`.
    """
    root = root.resolve()
    p = root
    for part in parts:
        if part is None:
            raise ValueError("path component is None")
        p = (p / part)
    rp = p.resolve()
    if rp != root and root not in rp.parents:
        raise ValueError(f"path escapes {root}: {rp}")
    return rp
