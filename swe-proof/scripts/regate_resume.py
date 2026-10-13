#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Construct-or-regate driver: bring one cell, a lane, or every (instance,
backend) cell of a benchmark to strict fully-green, resumably.

This is the ONLY entry point for "re-judge a whole cell". Cells are worked from a
thread pool holding the same per-cell flock the authoring fleets hold, so a cell
another driver owns is skipped rather than measured mid-edit.
`scripts/restamp_gate.py` is the right tool for the other half of the work:
re-measuring a NAMED subset of gates, minutes per cell, when the rest of the cell
is not in question.

Per-cell state machine (decided fresh from meta.json on every run, so the
script is safe to kill and relaunch -- already-green cells cost one classify):

  1. strictly GREEN (green_check.classify)          -> skip (unless --force)
  2. principled BLOCKED (BLOCKED.md, no solution)   -> skip (parked by design)
  3. no solution file at all                        -> CONSTRUCT (build_one)
  4. otherwise (exists but not green)               -> REGATE:
       a. run every mechanical gate whose stamp is missing or non-ok
       b. if G-AX still fails: validate the bundle's axiom_check.py against
          the GOLD-patched tree; iff it passes there and the flag is absent,
          set ax_apply_gold and re-stamp through the real gate (some older
          probes were authored against the patched tree)
       c. if all mechanical gates are green and the audit is incomplete
          (G-EQ / panel roles missing or failed): run the agentic audit stage.
          When it is NOT run, say whether the records left in place still
          describe what is shipping -- see `_audit_skip_note`
       d. re-classify; report GREEN / NOTGREEN with the blocking gates

`green_check.classify` is the only authority for (1) and (d). Nothing here
re-derives greenness: a driver that counts its own fixes disagrees with the
release gate about exactly the cells it was repairing.

Environment (defaults set here, each overridable):
  SBU_BENCHMARK / SBU_BENCHMARK_DIR   required, as for every driver
  SBU_AUDIT_TIMEOUT=10800             per-role audit wall clock
  SBU_ATTACK_VERIFY_TIMEOUT=1200      per-attack verifier cap inside a role
  SBU_PBT_VERIFY_TIMEOUT=1800         G-PBT's verifier cap; an error at the gate's
                                      own default is usually a timeout
  SBU_MUTATION_WORKERS                mutant verifier fan-out, defaulted per
                                      backend; see `_mutation_workers`
  SBU_PYTHON                          interpreter for respawns

Both audit caps are sized against a CONTENDED verifier rather than an idle one: a
guillotined role yields an empty payload, which is recorded as a bogus "0 attacks"
INCONCLUSIVE audit failure, so an undersized cap manufactures spec defects instead
of merely slowing the lane down.

Usage:
  SBU_BENCHMARK_DIR=<corpus> python scripts/regate_resume.py \
      --benchmark-dir <corpus> --backends lean [velvet nagini] [--jobs 24] \
      [--limit N] [--dry-run] [--no-construct] [--no-audit] [--instances ...]

`--backends` is processed sequentially on purpose, one audit workload at a time:
Lean audits false-timeout when two overlap. Exit 0 iff every cell this pass looked
at ended GREEN, so a single-cell invocation is directly usable as a check.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _under_root(value: str) -> Path:
    """A benchmark root spelled as `paths.TASKS_ROOT` spells it: a relative value
    hangs off the PROJECT ROOT, not the cwd. Resolving against the cwd is how a
    relative `SBU_BENCHMARK_DIR` doubles into `<dir>/<dir>` for a caller outside
    the repo root, leaving the two halves of this script disagreeing about which
    cell they are looking at."""
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


def _export_benchmark_dir(argv: list[str]) -> None:
    """Make `--benchmark-dir` the root the GATES resolve against, not just the
    root this script scans.

    `paths.TASKS_ROOT` is read from `SBU_BENCHMARK_DIR` ONCE, at import time, and
    falls back to `benchmark`; `run_gates` resolves every artifact through it and
    takes no root argument. Without this the flag reaches only `plan_cell` and the
    cell lock, so a caller who passes it and forgets the variable classifies the
    real corpus and then stamps a freshly created stub bundle under the fallback
    root -- a red verdict about a bundle the run materialized itself.

    Duplicated from `restamp_gate._export_benchmark_dir` rather than imported:
    that module runs its own copy against `sys.argv` as an import side effect, so
    importing it here would parse this process's flags a second time invisibly.
    """
    want = ""
    for i, a in enumerate(argv):
        if a == "--benchmark-dir" and i + 1 < len(argv):
            want = argv[i + 1]
        elif a.startswith("--benchmark-dir="):
            want = a.split("=", 1)[1]
    if not want:
        return
    have = os.environ.get("SBU_BENCHMARK_DIR")
    if have and _under_root(have) != _under_root(want):
        raise SystemExit(
            f"--benchmark-dir {want!r} disagrees with SBU_BENCHMARK_DIR "
            f"{have!r}; the gates would resolve against the second and the "
            f"classification against the first")
    os.environ["SBU_BENCHMARK_DIR"] = want


_export_benchmark_dir(sys.argv)

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from swebench_unified.greenness import GREEN_OK as OK  # noqa: E402
from swebench_unified.backends.registry import BACKENDS  # noqa: E402
from swebench_unified.paths import EXPERIMENTS_ROOT  # noqa: E402
SOLUTION = {"nagini": "model.py", "velvet": "Solution.lean",
            "lean": "Solution.lean", "ears": "requirements.md"}
# The audit RECORDS, roles included, which is not `gates.AUDIT_GATES` (that is the
# two gate modules). Mirrors `check_stamp_freshness._AUDIT_GATES`, whose
# classification `_audit_skip_note` reads.
AUDIT_RECORDS = ("G-EQ", "G-PANEL", "G-PANEL-1", "G-PANEL-2", "G-PANEL-3")


# ---------------------------------------------------------------- classify --

def plan_cell(root: Path, iid: str, backend: str,
              force: bool = False) -> tuple[str, str]:
    """-> (action, note); action in green|blocked|construct|regate.

    `force` re-gates a cell that classifies GREEN, which is the one case this
    driver cannot see on its own: `classify` reads gate STATUSES and deliberately
    says nothing about stamp freshness, so a cell whose spec was edited after its
    stamps were taken is still GREEN here. The remedies for the two halves of that
    differ -- `check_stamp_freshness.py` for the mechanical gates,
    `audit_freshness.py` for the audit records -- so it stays an explicit request.
    """
    from green_check import classify
    bundle = root / iid / backend
    sol = bundle / SOLUTION[backend]
    # Classified once, and only the verdict decides: `force` disables the green
    # SKIP and nothing else, so a cell with no solution still routes to construct
    # (or stays parked) rather than being gated with nothing in it.
    verdict, why = classify(bundle, backend, iid) if bundle.is_dir() \
        else ("", "no bundle")
    if verdict == "GREEN" and not force:
        return "green", ""
    if (bundle / "BLOCKED.md").exists() and not sol.exists():
        return "blocked", "principled BLOCKED (parked by design)"
    if not sol.exists():
        return "construct", "no solution file"
    return "regate", ("GREEN but --force: re-measuring"
                      if verdict == "GREEN" else why)


# --------------------------------------------------------------- construct --

def do_construct(iid: str, backend: str) -> str:
    from swebench_unified.construct.build_one import build_one
    out = build_one(iid, backend)
    return f"construct -> {out.get('final_status')} ({out.get('note', '')[:60]})"


# ------------------------------------------------------------------ regate --

def _fix_ax_apply_gold(root: Path, iid: str, backend: str) -> str | None:
    """G-AX fails and the bundle predates the base-commit default: validate
    against the gold tree before opting in. Returns a note or None."""
    from swebench_unified.docker_exec import run_in_container
    from swebench_unified.gates import run_gates
    bundle = root / iid / backend
    meta_p = bundle / "meta.json"
    meta = json.loads(meta_p.read_text())
    if meta.get("ax_apply_gold"):
        return None  # already opted in; the failure is real
    patch = root / iid / "patch.diff"
    if not patch.exists() or not (bundle / "axiom_check.py").exists():
        return None
    r = run_in_container(iid, str(bundle.resolve()), "axiom_check.py",
                         gold_patch_path=str(patch.resolve()),
                         apply_gold=True, timeout=1800)
    if r.returncode != 0:
        return "G-AX fails even with gold applied (real failure)"
    meta["ax_apply_gold"] = True
    meta.setdefault("ax_apply_gold_note", (
        "pre-unification axiom_check.py exercises post-patch APIs; validated "
        "pass-with-gold / fail-at-base before opting in (regate_resume.py)"))
    # Atomically, like every other writer of a corpus record: a plain write_text
    # leaves meta.json truncated if this driver is killed mid-write, which
    # `green_check.classify` then reads as NOTGREEN.
    from swebench_unified.atomic_io import write_json_atomic
    write_json_atomic(meta_p, meta, sort_keys=True)
    res = run_gates(iid, backend, ["G-AX"], mode="strict", record=True)
    return f"ax_apply_gold set, G-AX re-stamped {res[0].status}"


def _audit_skip_note(bundle: Path, backend: str) -> str:
    """`skipped`, or `stale-not-rerun(<why>)`, for a pass that did not reach the
    agentic stage.

    The stage runs only when every mechanical gate is ok, because an attack battery
    aimed at a bundle that does not verify measures nothing. That makes the skip
    easy to misread once the spec has been edited: the G-EQ / G-PANEL records left
    in place were written about the spec BEFORE the edit and read afterwards as a
    fresh judgment of what is shipping.

    TWO authorities, because a content digest is the wrong question for an audit
    and the right one for the artifacts it cited:

    * `audit_freshness.verdict_for` decides whether the SPECIFICATION moved, by
      `markers.spec_signature` -- the case a digest check cannot see. It reports an
      audit gate's mismatch as `deferred`, since a comment edit or an added
      obligation does not stale an audit.
    * `check_stamp_freshness.check_cell` makes the two findings a content check CAN
      make about an audit record: a positive control that lost a clause
      (`changed`) and a cited artifact that is gone (`vanished`).

    Never raises: an unreadable bundle is the gates' problem to report, and a
    git-less checkout must not turn a re-gate into a crash.
    """
    why: list[str] = []
    try:
        from audit_freshness import verdict_for
        v, detail = verdict_for(bundle, backend)
        if v == "RE-AUDIT":
            why.append(f"spec moved: {detail}")
    except Exception:
        pass
    try:
        from check_stamp_freshness import check_cell
        moved = sorted({g for g, _f, kind in check_cell(bundle, set(AUDIT_RECORDS))
                        if kind in ("changed", "vanished")})
        if moved:
            why.append(",".join(moved))
    except Exception:
        pass
    return f"stale-not-rerun({'; '.join(why)})" if why else "skipped"


def do_regate(root: Path, iid: str, backend: str, audit: bool,
              force: bool = False) -> str:
    from green_check import classify
    from swebench_unified.greenness import conf_is_real_verdict
    from swebench_unified.gates import DOCKER_GATES, STATIC_GATES, run_gates
    from swebench_unified.construct.build_one import (final_status_of,
                                                      run_audit_stage)
    bundle = root / iid / backend
    meta_p = bundle / "meta.json"
    mech = list(STATIC_GATES) + list(DOCKER_GATES)
    notes: list[str] = []

    def gates_blob() -> dict:
        return json.loads(meta_p.read_text()).get("gates", {}) if meta_p.exists() else {}

    # (a) re-run missing or non-ok mechanical gates (recorded ok stamps are
    # trusted; a fresh judgment of a failing gate is the point of a re-gate).
    # --force re-runs all of them, the only way to refresh a stamp that is stale
    # rather than red: the caller is asking about the bytes, not the statuses.
    # Static before docker, so a static block does not spend Docker time.
    g = gates_blob()
    if force:
        run_gates(iid, backend, list(STATIC_GATES), mode="strict", record=True)
        g = gates_blob()
        if all(g.get(k, {}).get("status") in OK for k in STATIC_GATES):
            run_gates(iid, backend, list(DOCKER_GATES), mode="strict",
                      record=True)
        notes.append(f"mech re-ran {len(mech)} (--force)")
    else:
        to_run = [k for k in mech if g.get(k, {}).get("status") not in OK]
        if g.get("G-CONF", {}).get("status") in OK and not conf_is_real_verdict(g):
            to_run.append("G-CONF")  # pre-wiring placeholder skip is not a verdict
        if to_run:
            run_gates(iid, backend, to_run, mode="strict", record=True)
            notes.append(f"mech re-ran {len(to_run)}")

    # (b) G-AX apply-gold repair
    g = gates_blob()
    if g.get("G-AX", {}).get("status") not in OK:
        note = _fix_ax_apply_gold(root, iid, backend)
        if note:
            notes.append(note)

    # (c) audit iff mech fully green and audit incomplete
    g = gates_blob()
    mech_ok = all(g.get(k, {}).get("status") in OK for k in mech)
    roles = [g.get(f"G-PANEL-{n}", {}).get("status") for n in (1, 2, 3)]
    panel_done = (all(s in OK for s in roles)
                  or g.get("G-PANEL", {}).get("status") in OK)
    audit_done = g.get("G-EQ", {}).get("status") in OK and panel_done
    if audit and mech_ok and (force or not audit_done):
        from swebench_unified.agent import AgentAuthError
        try:
            ar = run_audit_stage(iid, backend)
            notes.append(f"audit {final_status_of(ar)}")
        except AgentAuthError:
            # Says nothing about this cell -- no agent authenticated, so the audit
            # gates are untouched and the cell stays on the worklist. Named so that
            # a lane whose whole pass reads "auth-outage" is legible as one host
            # condition rather than as a corpus of broken specs.
            notes.append("auth-outage (nothing recorded)")
        except Exception as e:
            notes.append(f"audit-error:{type(e).__name__}")
    else:
        notes.append(f"audit={_audit_skip_note(bundle, backend)}")

    v, why = classify(bundle, backend, iid)
    return f"regate -> {v}" + (f" ({why[:60]})" if v != "GREEN" else "") + \
        ((" :: " + "; ".join(notes)) if notes else "")


# ------------------------------------------------------------------ driver --

def _mutation_workers(backend: str) -> str:
    """G-MUT's verifier fan-out for this backend, unless the caller pinned it.

    `mut.py` defaults to 2, sized by "verifier processes the host can run without
    them slowing each other". A nagini cell fans out hundreds of solver
    invocations and this driver multiplies that by --jobs, and a mutant that
    misses its cap comes back with NO VERDICT rather than as a killed rival, so
    oversubscribing converts spec-strength evidence into unjudged mutants. One at
    a time there; the other backends' verifiers are cheap enough for the default.
    """
    return "1" if backend == "nagini" else "2"


def run_cell(root: Path, iid: str, backend: str, action: str,
             audit: bool, force: bool = False) -> tuple[str, str, str, float]:
    """Re-gate or construct one cell, under the per-cell lock every fleet holds.

    The lock is what makes it safe to run this lane alongside the authoring lanes.
    A cell's defect class is not fixed for the life of a run, so a cell that was
    only missing a stamp when this lane's list was built can be in an authoring
    lane minutes later; both drivers write meta.json, so one's stamps are lost and
    an artifact mid-edit gets gated half-written. Skipping a busy cell costs one
    pass of the lane, and the next pass picks it up.
    """
    from pbt_port_fleet import CellBusy, cell_lock
    t0 = time.monotonic()
    try:
        with cell_lock(root / iid / backend):
            if action == "construct":
                note = do_construct(iid, backend)
            else:
                note = do_regate(root, iid, backend, audit, force)
    except CellBusy as e:
        note = f"busy: held by {e}; skipped"
    except Exception as e:  # a crashing cell must not kill the pool
        note = f"{action} CRASHED: {type(e).__name__}: {str(e)[:100]}"
    return iid, backend, note, round(time.monotonic() - t0, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-dir", required=True)
    ap.add_argument("--backends", nargs="+", required=True,
                    choices=sorted(BACKENDS))
    ap.add_argument("--jobs", type=int, default=24)
    ap.add_argument("--limit", type=int, default=0, help="per backend")
    ap.add_argument("--no-construct", action="store_true",
                    help="only regate existing bundles")
    ap.add_argument("--no-audit", action="store_true",
                    help="mechanical gates only")
    ap.add_argument("--instances", nargs="*", default=None,
                    help="restrict to these instance ids (default: all)")
    ap.add_argument("--instances-file", default=None,
                    help="file of instance ids, one per line; a second "
                         "whitespace-separated field is read as a BACKEND, so "
                         "one lane file can carry per-cell targets")
    ap.add_argument("--audit-role-timeout", type=int, default=10800,
                    help="per-role wall clock for the agentic audit, seconds. "
                         "Size it against the loaded host: an overrun role is "
                         "recorded as an INCONCLUSIVE audit, not as a slow one")
    ap.add_argument("--attack-verify-timeout", type=int, default=1200,
                    help="per-attack verifier cap inside a role, seconds")
    ap.add_argument("--force", action="store_true",
                    help="re-measure a cell that already classifies GREEN "
                         "(every mechanical gate and a fresh audit stage). "
                         "Requires --instances or --instances-file")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # --force over the whole corpus is hours of agents per cell for cells that
    # nothing said were wrong, so it has to name its targets. The check is here
    # rather than in the parser because either restriction satisfies it.
    if args.force and not (args.instances or args.instances_file):
        ap.error("--force needs --instances or --instances-file: forcing a "
                 "fresh audit stage on every green cell in the corpus is "
                 "hours of agent time per cell")

    # A lane file may pin each instance to one backend (iid<TAB>backend), which
    # is what the green_check classification emits; a bare list applies to every
    # --backends entry.
    only: set[str] | None = None
    only_pairs: set[tuple[str, str]] = set()
    if args.instances:
        only = set(args.instances)
    if args.instances_file:
        only = only or set()
        for ln in Path(args.instances_file).read_text().split("\n"):
            parts = ln.split()
            if not parts:
                continue
            only.add(parts[0])
            if len(parts) > 1:
                only_pairs.add((parts[0], parts[1]))

    # Sized against the CONTENDED verifier: a role needs a conclusive result on at
    # least five attacks, each costing a verifier run, so a cap that fits a quiet
    # machine guillotines the role on a busy one -- see the module docstring.
    os.environ.setdefault("SBU_AUDIT_TIMEOUT", str(args.audit_role_timeout))
    # The attack verifier's own cap, distinct from the role's. An overrun verify is
    # inconclusive rather than a rejection (`adversary.check_attack`: "no verdict is
    # not a rejection"), which is the sound direction, but it costs the role an
    # attack it cannot replace and pushes it under the five it needs.
    os.environ.setdefault("SBU_ATTACK_VERIFY_TIMEOUT",
                          str(args.attack_verify_timeout))
    os.environ.setdefault("SBU_PBT_VERIFY_TIMEOUT", "1800")
    # Set per backend inside the loop, so remember whether the caller pinned it.
    workers_pinned = "SBU_MUTATION_WORKERS" in os.environ

    root = _under_root(args.benchmark_dir)
    log_dir = EXPERIMENTS_ROOT / "regate" / args.benchmark_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    rc = 0
    for backend in args.backends:  # sequential: one audit workload at a time
        # Safe to assign per backend because the backends run sequentially and
        # the pool is joined before the next one starts.
        if not workers_pinned:
            os.environ["SBU_MUTATION_WORKERS"] = _mutation_workers(backend)
        todo: list[tuple[str, str]] = []
        counts = {"green": 0, "blocked": 0}
        for inst in sorted(p.name for p in root.iterdir() if p.is_dir()):
            if only is not None and inst not in only:
                continue
            if only_pairs and (inst, backend) not in only_pairs:
                continue
            action, note = plan_cell(root, inst, backend, args.force)
            if action in ("green", "blocked"):
                counts[action] += 1
                continue
            if action == "construct" and args.no_construct:
                continue
            todo.append((inst, action))
        if args.limit:
            todo = todo[:args.limit]
        n_c = sum(1 for _, a in todo if a == "construct")
        print(f"[{backend}] skip: {counts['green']} green, "
              f"{counts['blocked']} blocked | todo: {len(todo)} "
              f"({n_c} construct, {len(todo)-n_c} regate) | jobs={args.jobs}",
              flush=True)
        if args.dry_run:
            for inst, a in todo[:15]:
                print(f"    {a:9s} {inst}")
            continue

        summary = log_dir / f"resume_{backend}.tsv"
        with summary.open("a") as sf, \
                ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futs = {pool.submit(run_cell, root, i, backend, a,
                                not args.no_audit, args.force): i
                    for i, a in todo}
            done = 0
            for fut in as_completed(futs):
                iid, bk, note, wall = fut.result()
                done += 1
                green = "-> GREEN" in note
                sf.write(f"{bk}\t{iid}\t{int(not green)}\t{wall}\t{note}\n")
                sf.flush()
                if not green or done % 10 == 0:
                    print(f"[{done}/{len(todo)}] {bk} {iid} ({wall}s) {note}",
                          flush=True)
                rc |= int(not green)
    return rc


if __name__ == "__main__":
    sys.exit(main())
