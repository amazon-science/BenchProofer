#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Drive a benchmark port end to end in a throwaway root, and report facts.

    python scripts/benchmark_smoke.py --root "$(mktemp -d)" --benchmark swe_gym_lite

Fetch a slice, freeze it, materialize one cell, assemble both prompt paths, run
every gate that can run without a model or a verifier, and write DIR/report.json.
Nothing is asserted here beyond what would make the report a lie: the caller
decides what the facts mean (tests/test_third_benchmark_smoke.py does exactly
that for the registered third benchmark, and a port can diff two reports).

This is the answer to "how do I know my port works": it needs a registry entry
(or SBU_BENCHMARK_SPEC), and it needs no code in this repository to know the
benchmark's name. The run is confined to --root -- the frozen slice, the bundle
corpus, the repository mirror, the HuggingFace cache and the run output all live
under it, so a port can be smoke-tested against a checkout it does not write
into.

Exit: 0 report written, 1 a defect in this pipeline, 2 usage, 3 upstream (the
dataset hub or git) was unreachable, which is not a verdict about the port.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXIT_DEFECT, EXIT_USAGE, EXIT_UNAVAILABLE = 1, 2, 3

# Stands in for a workdir no benchmark declares, so a prompt containing it can
# only have read the registry entry. See the sentinel step below.
SENTINEL_WORKDIR = "/smoke-sentinel-workdir"

# A specification for the cell, so the run needs no model. Deliberately about
# nothing: it names no file, no test and no identifier, which is what lets it
# stand in for any instance and still survive the leakage gate.
PLACEHOLDER_REQUIREMENTS = """\
# Requirements: the behaviour this task changes

## Introduction

This document stands in for the specification a construction agent writes, so
that a port can be exercised without a model. It states a requirement in the
shape the pipeline expects and deliberately describes no particular program.

## Requirement 1: the observable outcome is distinguishable

**User story:** As a caller of this component, I want each outcome of a request
to be reported distinguishably, so that I can tell what happened without
inspecting state I do not own.

**Acceptance criteria**

1. WHEN a request completes and changes stored state, THEN the component SHALL
   report the outcome that says state changed.
2. WHEN a request completes without changing stored state, THEN the component
   SHALL report the outcome that says nothing changed.
3. WHILE a caller is tracking outcomes across several requests, the component
   SHALL report each request exactly once.
"""


# ------------------------------------------------------------- the containment
def contained_roots(root: Path) -> dict[str, str]:
    """Every location this run reads or writes, moved under `root`.

    A dict rather than four `setdefault` calls inline, so the promise the module
    docstring makes is checkable by something other than reading it: a root added
    to paths.py and not to this dict leaves output in the checkout, and a smoke
    run that writes there still passes, which is how the run-output root stayed
    non-relocatable for as long as it did.
    """
    return {
        "SBU_DATA_ROOT": str(root / "data"),        # the frozen slice
        "SBU_BENCHMARK_DIR": str(root / "corpus"),  # the constructed bundle
        "SBU_REPOS_ROOT": str(root / "repos"),      # the task-repo mirror
        "SBU_EXPERIMENTS_DIR": str(root / "run"),   # logs, scratch, reports
        "HF_HOME": str(root / "hf"),                # the dataset cache
    }


# --------------------------------------------------------------- the contract
def frame_is_upstream(filename: str) -> bool:
    """Whether a traceback frame belongs to a dependency rather than to us.

    This is what keeps a smoke run from going vacuous. A fetch can fail because
    the hub is unreachable (not a verdict) or because our own seam is broken (a
    defect), and calling both "unavailable" hides the second: measured, a
    one-character typo in a `frozen_columns` entry makes the freeze raise
    KeyError, and reporting that as unavailability leaves a green suite.
    """
    filename = filename.replace(os.sep, "/")
    if "/site-packages/" in filename or "/dist-packages/" in filename:
        return True          # an installed dependency, even if it sits in-tree
    return not filename.startswith(str(PROJECT_ROOT))


def _raise_site_is_upstream(exc: BaseException) -> bool:
    tb, deepest = exc.__traceback__, ""
    while tb is not None:                       # the raise site, not the caller
        deepest = tb.tb_frame.f_code.co_filename
        tb = tb.tb_next
    return frame_is_upstream(deepest)


def _patched_paths(diff: str) -> list[str]:
    """Files the gold patch touches, from its `+++ b/...` headers."""
    return [m.group(1) for m in re.finditer(r"^\+\+\+ b/(.+)$", diff, re.M)]


# ------------------------------------------------------------------- the run
def drive(args) -> tuple[int, dict]:
    """A linear script, read top to bottom. Returns (exit code, report)."""
    root = Path(args.root)
    report: dict = {}
    out = root / "report.json"

    def save() -> None:
        out.write_text(json.dumps(report, indent=2, sort_keys=True))

    def fail(msg: str) -> tuple[int, dict]:
        report["error"] = msg
        save()
        return EXIT_DEFECT, report

    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    import fetch_dataset

    from swebench_unified import benchmarks as bm
    if args.benchmark not in bm.registry():
        return fail(f"unknown benchmark {args.benchmark!r}; known: "
                    f"{sorted(bm.registry())} (declare another with "
                    f"{bm.SPEC_ENV})")

    # --- 1. fetch and freeze a slice -------------------------------------
    t0 = time.monotonic()
    try:
        rc = fetch_dataset.main(["--benchmark", args.benchmark,
                                 "--limit", str(args.rows)])
    except Exception as e:      # noqa: BLE001 - classified, not swallowed
        if not _raise_site_is_upstream(e):
            return fail("fetch_dataset raised inside the checkout -- a seam "
                        f"defect, not unavailability:\n"
                        f"{traceback.format_exc()[-1500:]}")
        report["unavailable"] = f"could not fetch: {type(e).__name__}: {e}"
        save()
        return EXIT_UNAVAILABLE, report
    if rc != 0:
        # NOT unavailable: a non-zero return is the column contract refusing an
        # upstream schema drift, which is a real answer about the port.
        return fail(f"fetch_dataset.main returned {rc} (schema drift?)")

    from swebench_unified import paths
    from swebench_unified.construct import build_one
    from swebench_unified.gates import DOCKER_GATES, STATIC_GATES, run_gates
    from swebench_unified.gates.base import load_frozen_row

    bench = bm.active()
    frozen = bench.dataset_jsonl
    rows = [json.loads(ln) for ln in frozen.read_text().splitlines()]
    report["fetch"] = {
        "rows": len(rows), "repos": len({r["repo"] for r in rows}),
        "path": str(frozen), "seconds": round(time.monotonic() - t0, 1),
        "sha256": hashlib.sha256(frozen.read_bytes()).hexdigest(),
    }
    report["resolve"] = {
        "active": bench.name, "dataset_jsonl": str(paths.DATASET_JSONL),
        "tasks_root": str(paths.TASKS_ROOT), "data_root": str(bm.data_root()),
    }
    # The row contract is `fetch_dataset.row_complaints`, the same checker the
    # freeze enforces per row before it writes anything -- asked again HERE
    # because these are the bytes that were written, so `key_order=True`: the
    # declared column order is part of what G-INTEGRITY compares, and only a row
    # read back out of the frozen file can be asked about it. A second copy of
    # the rule would be the thing this script exists to catch, one level up.
    report["schema"] = {
        "ids": sorted(r["instance_id"] for r in rows),
        "columns": list(rows[0]),
        "complaints": [f"{r['instance_id']}: {c}" for r in rows
                       for c in fetch_dataset.row_complaints(r, bench,
                                                             key_order=True)],
    }
    save()

    iid = args.instance or report["schema"]["ids"][0]
    row = load_frozen_row(iid)          # the gates' own reader, not our parse
    if row is None:
        # Say so here, or the next step dies of `None['patch']` deep inside
        # build_one and the report is never written.
        return fail(f"{iid} is not in the frozen slice "
                    f"{report['schema']['ids']}: the split, the sort order or "
                    "hf_split changed")
    report["instance"] = iid

    # --- 2. P0: freeze the inputs, materialize the worktree --------------
    repo = row["repo"]
    # `setup_repos.clone_url`, not a literal host: the documented mirror step
    # reads the benchmark's `repo_url_template`, so a benchmark whose repos are
    # not on GitHub is meant to need no code -- and a smoke run that hardcoded
    # GitHub would clone the wrong thing while reporting a successful port.
    import setup_repos
    clone_url = args.clone_url or setup_repos.clone_url(repo)
    # `paths.mirror_dir`, because this clones the mirror that build_one.prepare
    # then reads: a second spelling here clones under a name `prepare` never
    # looks for, and the report blames the worktree instead of the clone.
    mirror = paths.mirror_dir(repo)
    clone_err = ""
    if args.clone and not mirror.exists():
        mirror.parent.mkdir(parents=True, exist_ok=True)
        # setup_repos.py uses a full `git clone --bare`; blobless is enough for
        # one worktree and keeps a smoke run to a few MB.
        c = subprocess.run(["git", "clone", "--filter=blob:none", "--bare",
                            clone_url, str(mirror)],
                           capture_output=True, text=True, timeout=args.timeout)
        clone_err = "" if c.returncode == 0 else f"clone failed: {c.stderr[-300:]}"
    elif not args.clone:
        clone_err = "no repo clone (--no-clone)"
    wt, err = build_one.prepare(iid, args.backend, row)
    inst = paths.instance_dir(iid)
    touched = _patched_paths(row["patch"])
    report["prepare"] = {
        "error": clone_err or err,
        "clone_url": clone_url,
        "instance_json_matches_frozen_row":
            json.loads((inst / "instance.json").read_text()) == row,
        "patch_diff_bytes": len((inst / "patch.diff").read_text()),
        "patched_paths": touched,
        "worktree": str(wt),
        "worktree_head": subprocess.run(
            ["git", "-C", str(wt), "rev-parse", "HEAD"], capture_output=True,
            text=True).stdout.strip() if not err else "",
        "worktree_has_patched_files":
            all((wt / p).exists() for p in touched) if (touched and not err)
            else None,
    }
    save()

    try:
        # --- 3. the bundle a construction agent would have written -------
        bundle = paths.bundle_dir(iid, args.backend)
        bundle.mkdir(parents=True, exist_ok=True)
        requirements = (Path(args.requirements).read_text()
                        if args.requirements else PLACEHOLDER_REQUIREMENTS)
        (bundle / "requirements.md").write_text(requirements)
        meta_p = bundle / "meta.json"
        meta = json.loads(meta_p.read_text())     # prepare() stamped provenance
        meta["spec_sources"] = ["issue"]          # the hygiene gate requires one
        meta_p.write_text(json.dumps(meta, indent=2))

        # --- 4. prompts, both paths, no model ---------------------------
        import dataclasses

        from swebench_unified.eval.adapter import get_adapter
        from swebench_unified.eval.dataset import (as_dict, assert_no_leak,
                                                  build_task)
        from swebench_unified.eval.prompts import initial_user, system_prompt
        from swebench_unified.prompts import load_prompt

        adapter = get_adapter(args.backend)
        task = build_task(adapter, iid, mode=7)   # mode 7: issue + spec view
        task_dict = as_dict(task)
        assert_no_leak(task_dict)
        report["prompts"] = {
            "workdir": bm.active_workdir(),
            "construct_system": load_prompt("construct_system",
                                            backend=args.backend),
            "worker": load_prompt("worker", backend=args.backend, iid=iid,
                                  root=paths.tasks_root_rel()),
            "eval_system": system_prompt(adapter, task),
            "eval_user": initial_user(adapter, task),
            "task_dict": task_dict,
            "requirements_md": requirements,
        }
        # The same prompt with the ENTRY's workdir replaced. Without this the
        # workdir facts cannot be read: a benchmark that declares the default
        # /testbed makes "the prompt names /testbed" equally true of a
        # re-hardcoded literal. Measured -- `active_workdir()` replaced by
        # `return "/testbed"` left the end-to-end assertions passing.
        # Swap `registry()`, not the REGISTRY dict: an externally declared
        # benchmark is not in that dict, and mutating it would leave the
        # sentinel unread for exactly the ports this script exists to check.
        known = bm.registry()
        entry = known.get(args.benchmark)
        if entry is not None:
            swapped = dict(known, **{args.benchmark: dataclasses.replace(
                entry, container_workdir=SENTINEL_WORKDIR)})
            real = bm.registry
            bm.registry = lambda: swapped
            try:
                report["prompts"]["eval_system_sentinel"] = system_prompt(
                    adapter, task)
                report["prompts"]["workdir_sentinel"] = bm.active_workdir()
            finally:
                bm.registry = real
        # Nothing above may have reached a model. Read off sys.modules: the
        # agent SDK is not even imported, so no credential, slot or network
        # call can have happened.
        report["no_model"] = [m for m in ("swebench_unified.agent",
                                         "claude_agent_sdk",
                                         "swebench_unified.eval.run")
                              if m in sys.modules]
        save()

        # --- 5. the gates ------------------------------------------------
        results = run_gates(iid, args.backend,
                            list(STATIC_GATES) + list(DOCKER_GATES), record=True)
        report["gates"] = [{"gate": g.gate, "status": g.status, "ok": g.ok,
                            "detail": g.detail, "data": g.data or {}}
                           for g in results]
        from swebench_unified.harness import run_resolve
        rr = run_resolve(iid, "diff --git a/x b/x\n")
        report["run_resolve"] = {"resolved": rr.resolved,
                                 "completed": rr.completed, "note": rr.note}

        # the control: tamper with the frozen inputs, the integrity gate must
        # refuse. Without it a passing G-INTEGRITY says nothing.
        good = (inst / "instance.json").read_text()
        tampered = dict(row,
                        problem_statement=row["problem_statement"] + " (edited)")
        (inst / "instance.json").write_text(json.dumps(tampered))
        control = {"tampered": run_gates(iid, args.backend, ["G-INTEGRITY"],
                                         record=False)[0].status}
        (inst / "instance.json").write_text(good)
        control["restored"] = run_gates(iid, args.backend, ["G-INTEGRITY"],
                                        record=False)[0].status
        report["integrity_control"] = control
        save()

        # --- 6. the release gate over the one-cell corpus ---------------
        report["release_gate"] = {}
        for only in ("prose", "green"):
            p = subprocess.run(
                [sys.executable, str(PROJECT_ROOT / "scripts" / "release_gate.py"),
                 "--benchmark-dir", str(paths.TASKS_ROOT),
                 "--benchmark", args.benchmark, "--backends", args.backend,
                 "--only", only, "--timeout", "600"],
                capture_output=True, text=True, timeout=args.timeout,
                cwd=str(PROJECT_ROOT))
            report["release_gate"][only] = {
                "returncode": p.returncode,
                "tail": ((p.stdout or "") + (p.stderr or ""))[-2500:]}
            save()
    finally:
        if not report.get("prepare", {}).get("error"):
            build_one.cleanup_worktree(iid, args.backend, row)
        save()
    return 0, report


def _summary(report: dict) -> str:
    lines = []
    f, s = report.get("fetch", {}), report.get("schema", {})
    lines.append(f"instance      {report.get('instance', '-')}")
    lines.append(f"frozen        {f.get('rows', 0)} rows, {f.get('repos', 0)} "
                 f"repo(s), sha256 {f.get('sha256', '-')[:16]}")
    lines.append(f"schema        {len(s.get('complaints', []))} complaint(s)")
    for c in s.get("complaints", [])[:8]:
        lines.append(f"              {c}")
    prep = report.get("prepare", {})
    lines.append(f"worktree      {prep.get('worktree_head', '')[:12] or '-'}"
                 + (f"  ({prep['error']})" if prep.get("error") else ""))
    by = {}
    for g in report.get("gates", []):
        by.setdefault(g["status"], []).append(g["gate"])
    lines.append("gates         " + "; ".join(
        f"{k}: {' '.join(sorted(v))}" for k, v in sorted(by.items())) or "-")
    ic = report.get("integrity_control", {})
    lines.append(f"integrity     tampered={ic.get('tampered', '-')} "
                 f"restored={ic.get('restored', '-')}")
    for only, r in sorted(report.get("release_gate", {}).items()):
        lines.append(f"release/{only:<6}exit {r['returncode']}")
    if report.get("no_model"):
        lines.append(f"MODEL PATH IMPORTED: {report['no_model']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="benchmark-smoke",
        description="drive a benchmark port end to end in a throwaway root")
    ap.add_argument("--root", required=True, metavar="DIR",
                    help="throwaway root; every path the run reads or writes "
                         "goes under it (data, corpus, repos, HF cache, run "
                         "output)")
    ap.add_argument("--benchmark", required=True, metavar="NAME",
                    help="registry name, including one declared by "
                         "SBU_BENCHMARK_SPEC")
    ap.add_argument("--instance", default="", metavar="IID",
                    help="which instance to build (default: first of the slice)")
    ap.add_argument("--backend", default="ears",
                    help="specification backend (default: ears, the one with no "
                         "verifier, so a smoke run needs no prover installed)")
    ap.add_argument("--rows", type=int, default=4, metavar="N",
                    help="freeze the first N rows by instance id (default 4)")
    ap.add_argument("--clone-url", default="", metavar="URL",
                    help="mirror source (default: the benchmark's "
                         "repo_url_template applied to the row's repo)")
    ap.add_argument("--no-clone", dest="clone", action="store_false",
                    help="skip the mirror; the worktree step then reports why")
    ap.add_argument("--requirements", default="", metavar="FILE",
                    help="specification for the cell (default: a placeholder "
                         "that describes no particular program)")
    ap.add_argument("--timeout", type=int, default=1800, metavar="SEC",
                    help="per-subprocess timeout (default 1800)")
    args = ap.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f"--root {root} is not a directory", file=sys.stderr)
        return EXIT_USAGE
    # Set the roots BEFORE importing the package: paths.py binds its locations at
    # import, so a run configured afterwards would aim the freeze at the real
    # data root. This is a fresh process, so doing it here is enough -- and it
    # is why this is a script rather than a library call.
    os.environ.setdefault("SBU_BENCHMARK", args.benchmark)
    for var, value in contained_roots(root).items():
        os.environ.setdefault(var, value)
    os.environ.setdefault("SBU_RUN_PREFIX", f"smoke{os.getpid()}")
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

    rc, report = drive(args)
    if report.get("unavailable"):
        print(f"UNAVAILABLE: {report['unavailable']}", file=sys.stderr)
    elif report.get("error"):
        print(f"DEFECT: {report['error']}", file=sys.stderr)
    else:
        print(_summary(report))
    print(f"\nreport -> {root / 'report.json'} (exit {rc})")
    return rc


if __name__ == "__main__":
    sys.exit(main())
