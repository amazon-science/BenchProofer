# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Parallel construction runner.

Fans build_one out N-way, one SUBPROCESS per instance (a fatal error cannot
poison siblings), with a hard per-instance wall clock (SIGTERM then SIGKILL;
build_one's SIGTERM handler cleans its /tmp worktree).

Instances are shuffled with a fixed seed so any PREFIX of the run is a uniform
random sample (a partial run is representative). Resumable: build_one skips
already-green bundles unless --force. Joblog + per-instance stdout logs under
experiments/construct/<backend>/.

`--dry-run` reports the worklist and every precondition and launches nothing,
because the real thing spends one agent run per cell.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .. import paths
from ..backends.registry import BACKENDS

DEFAULT_SEED = 1776
DEFAULT_JOBS = 12
DEFAULT_WALL = 7200  # 8 construct rounds + Docker gates fit in 2h


def all_instance_ids() -> list[str]:
    ids = []
    with paths.DATASET_JSONL.open() as fh:
        for line in fh:
            if line.strip():
                ids.append(json.loads(line)["instance_id"])
    return ids


def worklist(ids: list[str], seed: int, limit: int) -> list[str]:
    """Deterministic shuffle + optional prefix limit."""
    ids = list(ids)
    random.Random(seed).shuffle(ids)
    return ids[:limit] if limit > 0 else ids


def sweep_stale_worktrees(backend: str) -> int:
    """Pre-flight: remove orphaned /tmp worktrees left by a SIGKILLed run, which
    exhaust the tmpfs inode table if they pile up. Only OUR run-prefixed ones."""
    pattern = f"wt_{paths.RUN_PREFIX}_{backend}_*"
    stale = sorted(Path("/tmp").glob(pattern))
    for wt in stale:
        for mirror in sorted(paths.REPOS_ROOT.glob("*.git")):
            r = subprocess.run(["git", "--git-dir", str(mirror), "worktree",
                                "remove", "--force", str(wt)], capture_output=True)
            if r.returncode == 0:
                break
        shutil.rmtree(wt, ignore_errors=True)
    for mirror in sorted(paths.REPOS_ROOT.glob("*.git")):
        subprocess.run(["git", "--git-dir", str(mirror), "worktree", "prune"],
                       capture_output=True)
    return len(stale)


def run_one_subprocess(instance_id: str, backend: str, wall_seconds: int,
                       extra: list[str], log_dir: Path) -> tuple[str, int, float]:
    """Run build_one in an isolated subprocess with a hard wall (SIGTERM at
    the wall, SIGKILL 60s later). Returns (instance_id, returncode, wall_s)."""
    cmd = [paths.python_bin(), "-m", "swebench_unified.construct.build_one",
           "--backend", backend, "--instance", instance_id, *extra]
    log_path = log_dir / f"{instance_id}.log"
    start = time.monotonic()
    with log_path.open("ab") as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                cwd=str(paths.PROJECT_ROOT),
                                start_new_session=True)

        def _signal_group(sig: int) -> None:
            # signal the whole start_new_session process group, or
            # grandchildren (agent CLI, verifier, docker) outlive the wall
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError:
                pass

        try:
            rc = proc.wait(timeout=wall_seconds)
        except subprocess.TimeoutExpired:
            _signal_group(signal.SIGTERM)  # build_one cleans its worktree
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                _signal_group(signal.SIGKILL)
                proc.wait()
            rc = 124
    if rc == 124:
        # build_one's SIGTERM handler deliberately writes no result.json;
        # persist a terminal timeout record so resume can tell a timed-out
        # instance from one that never ran.
        _persist_timeout_result(instance_id, backend, wall_seconds)
    return instance_id, rc, round(time.monotonic() - start, 1)


def _persist_timeout_result(instance_id: str, backend: str,
                            wall_seconds: int) -> None:
    p = paths.bundle_dir(instance_id, backend) / "result.json"
    try:
        existing = json.loads(p.read_text()).get("final_status")
    except (FileNotFoundError, json.JSONDecodeError):
        existing = None
    if existing in ("ok", "blocked"):
        return  # child finished before the kill landed; its verdict stands
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "instance_id": instance_id, "backend": backend,
        "final_status": "timeout",
        "note": f"killed by the wall-clock limit ({wall_seconds}s)",
        "wall_time_s": wall_seconds,
    }, indent=2))


def _result_status(instance_id: str, backend: str) -> str:
    p = paths.bundle_dir(instance_id, backend) / "result.json"
    try:
        return json.loads(p.read_text()).get("final_status", "?")
    except (FileNotFoundError, json.JSONDecodeError):
        return "?"


def dry_run(backend: str, ids: list[str], *, jobs: int, wall_seconds: int,
            seed: int, extra: list[str]) -> int:
    """Report what a run WOULD do and launch nothing. Returns an exit code.

    `--all` is one credential-spending agent run per cell -- 500 of them for
    SWE-bench Verified -- and every precondition it needs is checked deep inside
    a child, per instance, after the fan-out has started. So the only way to find
    out that the dataset is for another benchmark, or that no provider is
    configured, used to be to start the run and read a fan of identical failures.

    Each precondition is asked of the ONE definition that decides it in a real
    run (`gates.base.frozen_dataset_complaint`, `agent.provider_preflight`,
    `paths.mirror_dir`, `build_one.already_green`), never restated here: a dry run
    that answers from its own copy of a rule is a dry run that can disagree with
    the thing it predicts.
    """
    from ..agent import provider_preflight
    from ..gates.base import frozen_dataset_complaint, load_frozen_row
    from . import build_one

    print(f"# dry run: nothing is launched\n"
          f"backend            {backend}\n"
          f"worklist           {len(ids)} instance(s), shuffled with seed {seed}\n"
          f"concurrency        {jobs}-way, {wall_seconds}s wall per instance\n"
          f"corpus root        {paths.TASKS_ROOT}\n"
          f"logs               {paths.EXPERIMENTS_ROOT / 'construct' / backend}\n"
          f"passed to each build   {' '.join(extra) or '(nothing)'}")

    blockers, warnings = [], []
    if (why := frozen_dataset_complaint()):
        blockers.append(why)
    if (why := provider_preflight()):
        blockers.append(why)

    # Per instance: what the run would skip, and what it could not even start.
    green = [i for i in ids if build_one.already_green(i, backend)]
    unknown = [i for i in ids if load_frozen_row(i) is None]
    mirrors: dict[str, list[str]] = {}
    for iid in ids:
        row = load_frozen_row(iid)
        if row:
            mirrors.setdefault(row["repo"], []).append(iid)
    missing = {r: v for r, v in mirrors.items() if not paths.mirror_dir(r).is_dir()}

    print(f"already green      {len(green)} would be skipped without --force")
    print(f"would build        {len(ids) - len(green)}")
    if unknown:
        blockers.append(f"{len(unknown)} instance(s) are not in the frozen dataset "
                        f"({', '.join(unknown[:3])}...): the worklist and "
                        f"{paths.DATASET_JSONL.name} disagree")
    if missing:
        n = sum(len(v) for v in missing.values())
        blockers.append(f"{len(missing)} task repo(s) have no mirror under "
                        f"{paths.REPOS_ROOT}, covering {n} instance(s): "
                        f"{', '.join(sorted(missing))}. Run "
                        f"`python scripts/setup_repos.py`")
    if not ids:
        warnings.append("the worklist is empty, so there is nothing to report "
                        "about; the blockers below are why")
    elif len(ids) == len(green):
        warnings.append("every instance in the worklist is already green; "
                        "without --force this run would build nothing")

    for w in warnings:
        print(f"NOTE  {w}")
    for b in blockers:
        print(f"BLOCKED  {b}")
    print(f"# {len(blockers)} blocker(s); "
          + ("a real run would fail per instance" if blockers
             else "nothing stops a real run"))
    return 1 if blockers else 0


def run_all(backend: str, ids: list[str], *, jobs: int = DEFAULT_JOBS,
            wall_seconds: int = DEFAULT_WALL,
            extra: list[str] | None = None) -> dict[str, int]:
    extra = list(extra or [])
    log_dir = paths.EXPERIMENTS_ROOT / "construct" / backend
    log_dir.mkdir(parents=True, exist_ok=True)
    joblog = log_dir / "joblog.tsv"
    swept = sweep_stale_worktrees(backend)
    if swept:
        print(f"[run_all] swept {swept} stale worktree(s)")
    print(f"[run_all] {len(ids)} instances, {jobs}-way, {wall_seconds}s wall, "
          f"backend={backend}, logs under {log_dir}")

    counts: dict[str, int] = {}
    with joblog.open("a") as jl, ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(run_one_subprocess, iid, backend, wall_seconds,
                               extra, log_dir): iid for iid in ids}
        for fut in as_completed(futures):
            iid, rc, wall = fut.result()
            status = "timeout" if rc == 124 else _result_status(iid, backend)
            counts[status] = counts.get(status, 0) + 1
            jl.write(f"{iid}\t{rc}\t{wall}\t{status}\n")
            jl.flush()
            print(f"[{iid}] rc={rc} status={status} ({wall}s)")
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="build many instances in parallel: fan build_one out over them")
    ap.add_argument("--backend", required=True, choices=sorted(BACKENDS))
    ap.add_argument("--only", nargs="*", default=None,
                    help="explicit instance ids (still shuffled)")
    ap.add_argument("--instances", default=None, metavar="FILE",
                    help="file with one instance id per line")
    ap.add_argument("--limit", type=int, default=0,
                    help="take the first N of the shuffled worklist (0 = all)")
    ap.add_argument("--jobs", type=int, default=DEFAULT_JOBS)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED,
                    help="deterministic shuffle seed (prefix = random sample)")
    ap.add_argument("--wall-seconds", type=int, default=DEFAULT_WALL,
                    help="hard per-instance wall clock")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the worklist and every precondition, launch "
                         "nothing (exit 1 if a real run would be blocked)")
    # unknown flags pass through to build_one; no `--` separator needed
    args, extra = ap.parse_known_args(argv)
    if extra and extra[0] == "--":
        extra = extra[1:]

    from ..gates.base import frozen_dataset_complaint

    if args.only:
        ids = list(args.only)
    elif args.instances:
        ids = [ln.strip() for ln in Path(args.instances).read_text().splitlines()
               if ln.strip()]
    else:
        # The whole-benchmark worklist IS the frozen dataset, so ask the one
        # definition of whether that dataset can answer for this corpus before
        # reading it. Nothing under `data/` is committed, so a checkout that has
        # not fetched yet -- the fresh-clone case -- otherwise gets a
        # FileNotFoundError traceback out of the driver's first line, including
        # from the dry run whose whole job is to report that precondition.
        ids = [] if frozen_dataset_complaint() else all_instance_ids()
    ids = worklist(ids, args.seed, args.limit)

    # Before the empty-worklist refusal: an empty worklist is one of the things
    # a dry run exists to explain.
    if args.dry_run:
        return dry_run(args.backend, ids, jobs=args.jobs,
                       wall_seconds=args.wall_seconds, seed=args.seed,
                       extra=extra)
    if not ids:
        why = frozen_dataset_complaint()
        print("no instances to run" + (f": {why}" if why else ""), file=sys.stderr)
        return 2

    counts = run_all(args.backend, ids, jobs=args.jobs,
                     wall_seconds=args.wall_seconds, extra=extra)
    print(f"[run_all] done: {counts}")
    return 0 if counts.get("blocked", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
