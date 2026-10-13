# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Central path configuration. Layout (docs/architecture.md §2): <root>/<instance_id>/
holds immutable inputs; <root>/<instance_id>/<backend>/ the constructed bundle.
<root> defaults to `benchmark/` (was `tasks/`), overridable via --benchmark-dir
/ SBU_BENCHMARK_DIR.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Dataset locations come from the ACTIVE benchmark (SBU_BENCHMARK, default
# swe_bench_verified) — see benchmarks.py, which also owns the data root
# (`benchmarks.data_root()`, SBU_DATA_ROOT). This module deliberately does NOT
# re-derive `PROJECT_ROOT / "data"`: two definitions diverge the moment the
# override is set. Imported here so existing `from ..paths import DATASET_JSONL`
# consumers are unchanged. eval_localization.json is precomputed offline so eval
# never opens the gold patch; eval_frozen.txt is the optional --frozen-list set.
from . import benchmarks as _benchmarks  # noqa: E402
from .corpus_root import default_benchmark_dir  # noqa: E402

_ACTIVE = _benchmarks.active()
DATASET_JSONL = _ACTIVE.dataset_jsonl
EVAL_LOCALIZATION = _ACTIVE.eval_localization
FROZEN_INSTANCES = _ACTIVE.frozen_instances

# Task-repo clones. No submodule/symlink: the user clones each repo themselves
# and either drops it under repos/<owner>_<name>.git or sets SBU_REPOS_ROOT, or
# points construction at one clone with `--repo PATH`.
REPOS_ROOT = Path(os.environ.get("SBU_REPOS_ROOT") or (PROJECT_ROOT / "repos"))
# Constructed-bundle root: <instance_id>/ (inputs) + <instance_id>/<backend>/
# (bundle). The default comes from `corpus_root`, which every corpus-walking
# tool's `--benchmark-dir` default also reads, so the two cannot name different
# trees; `--benchmark-dir NAME` (CLI) sets SBU_BENCHMARK_DIR, which survives the
# respawns a driver makes into build_one. An absolute value is used as-is; a bare
# name is taken under PROJECT_ROOT.
TASKS_ROOT = Path(default_benchmark_dir())
if not TASKS_ROOT.is_absolute():
    TASKS_ROOT = PROJECT_ROOT / TASKS_ROOT
# Run-output root: construction logs, eval artifacts, harness reports. Written
# to, unlike every other root here, so it is the one that has to be movable off
# the checkout -- a read-only or network-mounted clone cannot host it, and the
# official harness runs with this as its cwd. Same rule as TASKS_ROOT: an
# absolute value is used as-is, a bare name is taken under PROJECT_ROOT.
EXPERIMENTS_ROOT = Path(os.environ.get("SBU_EXPERIMENTS_DIR") or "experiments")
if not EXPERIMENTS_ROOT.is_absolute():
    EXPERIMENTS_ROOT = PROJECT_ROOT / EXPERIMENTS_ROOT
REPORTS_ROOT = EXPERIMENTS_ROOT / "reports"  # official-harness test-output logs (G-RESOLVE)
PROMPTS_ROOT = PROJECT_ROOT / "prompts"
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"

# Per-checkout isolation: Docker run-ids and /tmp worktrees are otherwise keyed
# only by instance_id, so concurrent checkouts would collide. Set SBU_RUN_PREFIX
# per checkout, else derive a stable hash of PROJECT_ROOT.
RUN_PREFIX = os.environ.get("SBU_RUN_PREFIX") or (
    "d" + hashlib.sha1(str(PROJECT_ROOT).encode()).hexdigest()[:8]
)


def python_bin() -> str:
    """Interpreter for self-respawns (a driver, the harness under a docker wrapper).
    A wrapper such as `sg` starts a fresh shell where a bare `python` may resolve
    to a system interpreter without our deps — use this, never "python".
    SBU_PYTHON overrides; default sys.executable."""
    import sys
    return os.environ.get("SBU_PYTHON") or sys.executable


def tasks_root_rel() -> str:
    """TASKS_ROOT as the agent sees it from its cwd (PROJECT_ROOT): relative
    when under the project, else absolute. Substituted into agent prompts as
    {root} — prompts must never hardcode the legacy `tasks/` name, or agents
    write bundles the pipeline never reads (SBU_BENCHMARK_DIR != tasks/)."""
    try:
        return str(TASKS_ROOT.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(TASKS_ROOT)


def mirror_dir(repo: str, root: Path | None = None) -> Path:
    """The bare mirror of a task repo: `<owner>_<name>.git` under REPOS_ROOT.

    One definition, because the step that CREATES a mirror and the three that READ
    it have to agree on the name. It was spelled four times -- scripts/setup_repos.py
    (the clone), construct/build_one.py, eval/adversary.py and
    scripts/build_eval_localization.py -- and a change on the clone side would have
    left the others looking for a directory nothing makes, reported as a worktree
    failure deep inside a build rather than as a missing mirror.

    `root` is for a caller that mirrors somewhere else (build_eval_localization
    takes the root on its command line); it defaults to the root every other step
    reads.
    """
    return (root or REPOS_ROOT) / (repo.replace("/", "_") + ".git")


def instance_dir(instance_id: str) -> Path:
    """Immutable per-instance inputs: instance.json, patch.diff."""
    return TASKS_ROOT / instance_id


def bundle_dir(instance_id: str, backend: str) -> Path:
    """Constructed bundle for one (instance, backend) pair."""
    return TASKS_ROOT / instance_id / backend
