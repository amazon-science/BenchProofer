#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Audit mode-3 self-constructed specs, blind to the downstream outcome.

Mode 8 measures spec correctness in isolation. Mode 3 has the agent construct a
spec AND turn it into a patch, so its saved artifacts let us ask the downstream
question: does a spec-correctness failure predict a failure to resolve the issue?

We reuse the mode-8 five-property adversarial judge (`grade.grade_spec`) verbatim
so the numbers stay comparable to the spec-synthesis table, and re-run it over every
`submission/<solution_filename>` saved by a from-scratch-spec run. The judge is
deliberately BLIND to:

  * whether the instance resolved / passed (the outcome we correlate against), and
  * the agent's own patch (the downstream artifact; showing it would let the judge
    infer the outcome from patch quality, and would conflate "is the spec correct"
    with "did the agent implement it").

It sees exactly what the mode-8 judge saw: the issue, the repo container, the
candidate spec, and the gold artifacts as behavioural ground truth. That keeps the
audit an independent variable, so the resolved/unresolved split is a real
correlation and not a self-fulfilling one.

Mode 3 is scored on equivalence, NOT on the spec audit (dataset.py:
MODES_SCORED_ON_SPEC == {11}), so `grade()` never ran this judge during the eval:
there is no cached verdict to reuse and no double-counting to worry about.

Writes, under experiments/eval/m4_spec_audit/<run_id>/:
    <instance_id>.json              the ballot record (mode-8 spec_audit shape)
    _abstained/<instance_id>.json    every ballot infra-failed; NOT cached, retried

Each instance is independent and resumable: the per-instance files ARE the progress
state, so re-running the same command after a creds rotation skips finished work.

    python scripts/eval/audit_scratch_specs.py --runs nagini-m4-opus-4.8-s1 ... \
        --judge-model opus-4.8 --votes 3 --concurrency 12
    python scripts/eval/audit_scratch_specs.py --runs ... --dry-run   # plan only
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from swebench_unified.backends.registry import GATED_BACKENDS  # noqa: E402
from swebench_unified.benchmarks import active as active_benchmark  # noqa: E402
from swebench_unified.eval import grade  # noqa: E402
from swebench_unified.eval.adapter import EvalAdapter, get_adapter  # noqa: E402
from swebench_unified.eval.dataset import MODES_SPEC_FROM_SCRATCH, build_task  # noqa: E402
from swebench_unified.eval.providers import MODEL_PRESETS, make_provider  # noqa: E402
from swebench_unified.eval.spec_impact import AUDIT_ROOT, EVAL_ROOT, run_config  # noqa: E402

# Instance-level fan-out, and the ONLY concurrency bound needed: grade_spec runs an
# instance's `votes` ballots SEQUENTIALLY, and a ballot holds at most one verifier
# subprocess (a Nagini JVM / Lean elaborator) or one axiom-probe container at a time.
# So concurrency N caps verifier processes at N. Most of a ballot's wall time is
# spent waiting on the judge model, not verifying, so N can exceed the core count.
DEFAULT_CONCURRENCY = 12

_print_lock = threading.Lock()


def log(msg: str):
    with _print_lock:
        print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def instances_of(run_id: str, adapter: EvalAdapter, need_grade: bool = True) -> list[str]:
    """Instances of a run that saved a non-trivial spec worth auditing.

    The spec filename is backend-dependent (model.py for nagini, Solution.lean for
    velvet/lean), so it comes from the adapter: hardcoding one would silently find
    zero instances for the other two backends.

    `need_grade` skips instances with no grade/result.json, since the analysis joins
    on it and an unjoinable ballot is wasted judge spend.
    """
    out = []
    for p in sorted((EVAL_ROOT / run_id).glob(f"*/submission/{adapter.solution_filename}")):
        idir = p.parent.parent
        if p.stat().st_size <= 50:
            continue
        if need_grade and not (idir / "grade" / "result.json").exists():
            continue
        out.append(idir.name)
    return out


def audit_one(run_id: str, iid: str, adapter: EvalAdapter, mode: int, judge_key: str,
              votes: int) -> dict:
    """One instance: N adversarial ballots on its spec. Blind to outcome + patch."""
    odir = AUDIT_ROOT / run_id
    odir.mkdir(parents=True, exist_ok=True)
    dst = odir / f"{iid}.json"
    if dst.exists():
        try:
            rec = json.loads(dst.read_text())
            if rec.get("spec_ok") is not None or rec.get("votes"):
                return {"instance_id": iid, "state": "cached"}
        except json.JSONDecodeError:
            pass                          # half-written by a killed run: redo it

    src = (EVAL_ROOT / run_id / iid / "submission" / adapter.solution_filename).read_text()
    # The ballot depends on the instance and the spec, not on the mode: build_task
    # withholds the gold artifacts and grade_spec reads them itself as behavioural
    # truth. The run's own mode is used so the task is exactly what it was graded on.
    task = build_task(adapter, iid, mode)
    # One provider per instance thread, not one shared across threads (each holds a
    # boto3 client). grade_spec takes a provider, not a factory.
    prov = make_provider({**MODEL_PRESETS[judge_key], "max_tokens": 8192})

    t0 = time.time()
    rec = grade.grade_spec(adapter, task, src, prov, votes=votes)
    rec.update(instance_id=iid, run_id=run_id, mode=mode, judge_model=judge_key,
               backend=adapter.backend.name, votes_requested=votes,
               wall_s=round(time.time() - t0, 1))

    # spec_ok is None exactly when every ballot infra-abstained (expired creds, a
    # dead container, a judge that never emitted a verdict). grade_spec swallows
    # those into the ballots rather than raising, so caching such a record would
    # freeze an infrastructure hiccup into the dataset forever. Park it instead.
    if rec.get("spec_ok") is None:
        park = odir / "_abstained"
        park.mkdir(exist_ok=True)
        (park / f"{iid}.json").write_text(json.dumps(rec, indent=2) + "\n")
        return {"instance_id": iid, "state": "abstained", "note": rec.get("note", "")}

    dst.write_text(json.dumps(rec, indent=2) + "\n")
    return {"instance_id": iid, "state": "done", "spec_ok": rec.get("spec_ok"),
            "wall_s": rec["wall_s"]}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="re-audit from-scratch specs, blind to the downstream outcome")
    ap.add_argument("--runs", nargs="+", required=True,
                    help="run ids under experiments/eval/, e.g. nagini-m4-opus-4.8-s1")
    ap.add_argument("--backend", choices=list(GATED_BACKENDS),
                    help="override; default reads each run's config.json")
    ap.add_argument("--mode", type=int, choices=sorted(MODES_SPEC_FROM_SCRATCH),
                    help="override; default reads each run's config.json")
    ap.add_argument("--judge-model", default="opus-4.8", choices=sorted(MODEL_PRESETS))
    ap.add_argument("--votes", type=int, default=3)
    ap.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    ap.add_argument("--limit", type=int, default=0, help="first N instances per run (pilot)")
    ap.add_argument("--allow-ungraded", action="store_true",
                    help="also audit instances with no grade/result.json (unjoinable)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the per-run plan and exit without calling a model")
    args = ap.parse_args()

    # Resolve backend + mode per run from its own config.json, so one command can
    # span backends and seeds; the flags override for runs predating config.json.
    plan: dict[str, tuple[EvalAdapter, int]] = {}
    for run_id in args.runs:
        if not (EVAL_ROOT / run_id).is_dir():
            print(f"!! no such run: {EVAL_ROOT / run_id}", file=sys.stderr)
            return 2
        cfg = run_config(run_id)
        bk, mode = args.backend or cfg.get("backend"), args.mode or cfg.get("mode")
        if not bk:
            print(f"!! {run_id}: no backend in config.json; pass --backend", file=sys.stderr)
            return 2
        if mode not in MODES_SPEC_FROM_SCRATCH:
            print(f"!! {run_id}: mode {mode} does not build a spec from scratch "
                  f"(need one of {sorted(MODES_SPEC_FROM_SCRATCH)}); pass --mode to override",
                  file=sys.stderr)
            return 2
        # The audit re-derives the task from the ACTIVE benchmark's frozen rows, so a
        # run built under the other benchmark would fail per instance with a confusing
        # "not in frozen dataset". Catch it once, up front.
        bench = cfg.get("benchmark")
        if bench and bench != active_benchmark().name:
            print(f"!! {run_id} was run under benchmark {bench!r} but SBU_BENCHMARK "
                  f"resolves to {active_benchmark().name!r}; re-run with "
                  f"SBU_BENCHMARK={bench}", file=sys.stderr)
            return 2
        plan[run_id] = (get_adapter(bk), mode)

    work: list[tuple[str, str]] = []
    for run_id in args.runs:
        adapter, _ = plan[run_id]
        iids = instances_of(run_id, adapter, need_grade=not args.allow_ungraded)
        work += [(run_id, i) for i in (iids[:args.limit] if args.limit else iids)]
    todo = [(r, i) for r, i in work if not (AUDIT_ROOT / r / f"{i}.json").exists()]

    if args.dry_run:
        for run_id in args.runs:
            adapter, mode = plan[run_id]
            n_all = sum(1 for r, _ in work if r == run_id)
            n_todo = sum(1 for r, _ in todo if r == run_id)
            print(f"[{run_id}] backend={adapter.backend.name} mode={mode} "
                  f"spec={adapter.solution_filename} auditable={n_all} "
                  f"todo={n_todo} cached={n_all - n_todo}")
        print(f"total: {len(work)} auditable, {len(todo)} to audit, "
              f"judge={args.judge_model} votes={args.votes} "
              f"concurrency={args.concurrency} benchmark={active_benchmark().name}")
        return 0

    # Interleave runs round-robin rather than draining run 1 before touching run 2.
    # The analysis needs all runs to progress together: a run-major order would leave
    # some seeds with zero data if the audit is stopped partway, while interleaved
    # order gives every run a comparable prefix.
    by_run: dict[str, list[str]] = {}
    for r, i in todo:
        by_run.setdefault(r, []).append(i)
    todo = [(r, by_run[r][k])
            for k in range(max((len(v) for v in by_run.values()), default=0))
            for r in args.runs if k < len(by_run.get(r, []))]
    log(f"{len(work)} auditable across {len(args.runs)} runs; {len(todo)} to audit "
        f"({len(work) - len(todo)} cached). judge={args.judge_model} "
        f"votes={args.votes} concurrency={args.concurrency}")

    done = abstained = failed = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(audit_one, r, i, *plan[r], args.judge_model, args.votes): (r, i)
                for r, i in todo}
        for fut in as_completed(futs):
            run_id, iid = futs[fut]
            n = done + abstained + failed + 1
            try:
                res = fut.result()
            except Exception as e:  # noqa: BLE001
                failed += 1
                log(f"[{n}/{len(todo)}] !! FAILED {run_id}/{iid}: {type(e).__name__}: {e}")
                traceback.print_exc(limit=2)
                continue
            if res["state"] == "abstained":
                abstained += 1
                log(f"[{n}/{len(todo)}] !! PARKED {run_id}/{iid} (all ballots "
                    f"infra-abstained; re-run to retry) {res['note'][:80]}")
            else:
                done += 1
                log(f"[{n}/{len(todo)}] {run_id}/{iid} spec_ok={res.get('spec_ok')} "
                    f"({res.get('wall_s')}s)  elapsed {(time.time()-t0)/60:.0f}m")

    log(f"finished: {done} audited, {abstained} parked, {failed} failed, "
        f"{(time.time()-t0)/60:.0f}m wall")
    if abstained or failed:
        log("re-run the same command to retry parked/failed instances (finished "
            "ones are cached)")
    return 0 if not (failed or abstained) else 1


if __name__ == "__main__":
    raise SystemExit(main())
