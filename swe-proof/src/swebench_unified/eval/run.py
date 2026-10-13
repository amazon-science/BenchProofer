# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Resumable parallel evaluation driver (--backend via the EvalAdapter).

Runs agent + grading over many instances, persisting every trajectory for
cheating review. Survives the 12h Bedrock credential rotation: each instance
builds a FRESH provider (re-reading creds); creds expiring mid-run PARK the
instance (status creds_expired) for resume rather than failing it.

Layout (experiments/eval/<run_id>/): config.json, summary.json, and per
instance: status.json, trajectory.jsonl (the audit surface), task.json
(assert-no-leak'd agent view), submission/, grade/result.json, audit.json,
adversary/record.json (audited modes only: the counterexample audit).

CLI:
  python -m swebench_unified.eval.run --backend lean --mode 4 --model opus-4.8 \
     --instances ... [--all] [--frozen-list FILE] [--instance-concurrency 4]
     [--run-id NAME] [--max-steps 60] [--judge-model opus-4.8] [--nuclear-sanitize]

`--all` = every row of the frozen dataset; pass `--frozen-list FILE` to evaluate
a fixed subset, so a partial run is comparable across models.
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

from ..paths import EXPERIMENTS_ROOT
from ..backends.registry import BACKENDS
from . import audit, grade, metrics
from .adapter import EvalAdapter, get_adapter
from .agent import EvalAgent
from .container import EvalContainer
from .dataset import all_instance_ids, as_dict as task_as_dict
from .dataset import assert_no_leak, build_task, frozen_instance_ids
from .providers import CredentialsExpired, MODEL_PRESETS, make_provider

EVAL_ROOT = EXPERIMENTS_ROOT / "eval"
# shared step budget across ALL modes (fair comparison); generous headroom, not
# a binding constraint
DEFAULT_EVAL_MAX_STEPS = 250
# "finished" states skipped on resume; everything else is re-run
DONE_STATES = {"done"}
RESUMABLE = {"pending", "error", "creds_expired", "running"}  # running = stale (crash)


def _run_dir(run_id: str) -> Path:
    return EVAL_ROOT / run_id


def _inst_dir(run_id: str, iid: str) -> Path:
    return _run_dir(run_id) / iid


def _read_status(run_id: str, iid: str) -> dict | None:
    p = _inst_dir(run_id, iid) / "status.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def _write_status(run_id: str, iid: str, **fields):
    d = _inst_dir(run_id, iid)
    d.mkdir(parents=True, exist_ok=True)
    cur = _read_status(run_id, iid) or {}
    cur.update(fields)
    (d / "status.json").write_text(json.dumps(cur, indent=2) + "\n")
    return cur


def _persist_trajectory(run_id: str, iid: str, trajectory: list):
    p = _inst_dir(run_id, iid) / "trajectory.jsonl"
    with p.open("w") as fh:
        for ev in trajectory:
            fh.write(json.dumps(ev) + "\n")


def run_one(adapter: EvalAdapter, run_id: str, iid: str, mode: int, model_key: str,
            judge_key: str | None, max_steps: int | None, bash_timeout: int,
            resolve_timeout: int, include_hints: bool, nuclear: bool) -> dict:
    idir = _inst_dir(run_id, iid)
    idir.mkdir(parents=True, exist_ok=True)
    # SAME step budget for ALL modes (fair cross-mode comparison)
    if max_steps is None:
        max_steps = DEFAULT_EVAL_MAX_STEPS
    t0 = time.time()
    _write_status(run_id, iid, instance_id=iid, mode=mode, model=model_key,
                  backend=adapter.backend.name, state="running", started_at=t0)

    try:
        task = build_task(adapter, iid, mode, include_hints=include_hints)
        tv = task_as_dict(task)
        assert_no_leak(tv)                       # never persist withheld fields
        (idir / "task.json").write_text(json.dumps(tv, indent=2) + "\n")

        # FRESH provider per instance → re-reads ~/.aws creds (12h rotation)
        prov = make_provider({**MODEL_PRESETS[model_key], "max_tokens": 4096})

        with EvalContainer(iid, task.base_commit, nuclear=nuclear) as c:
            cerr = c.start()
            if cerr:
                _write_status(run_id, iid, state="error", error=f"container: {cerr}",
                              ended_at=time.time())
                return {"instance_id": iid, "state": "error", "error": cerr}
            agent = EvalAgent(adapter, task, c, prov, max_steps=max_steps,
                              bash_timeout=bash_timeout)
            res = agent.run()

        _persist_trajectory(run_id, iid, res.trajectory)
        sub_dir = idir / "submission"
        sub_dir.mkdir(exist_ok=True)
        (sub_dir / "patch.diff").write_text(res.submission.patch or "")
        if res.submission.model_src is not None:
            (sub_dir / adapter.solution_filename).write_text(res.submission.model_src)

        # creds expiry mid-episode → PARK for resume
        if res.stop == "creds_expired":
            _write_status(run_id, iid, state="creds_expired", steps=res.steps,
                          usage=res.usage, error=res.error, ended_at=time.time())
            return {"instance_id": iid, "state": "creds_expired"}

        # audit: when the container stripped .git history, local git-history
        # flags are informational rather than disqualifying (see audit.py). Read
        # off the container, not passed as a literal: that demotion is the whole
        # of the difference between "the agent could not have read the fix" and
        # "the audit was told not to say so", and the sanitizer can decline.
        arep = audit.screen(iid, res.trajectory, sanitized=c.sanitized,
                            workdir=c.workdir)
        (idir / "audit.json").write_text(json.dumps(arep.as_dict(), indent=2) + "\n")

        judge = None
        if (task.scored_on_equivalence or task.scored_on_spec) and judge_key:  # modes 7, 3, 8
            # 8192: a reasoning judge emits analysis before the verdict JSON;
            # 1024 truncated it and miscounted the loss as a refutation
            judge = make_provider({**MODEL_PRESETS[judge_key], "max_tokens": 8192})
        g = grade.grade(adapter, task, res.submission.patch, res.submission.model_src,
                        run_id=f"{run_id}-{iid}", judge_provider=judge,
                        resolve_timeout=resolve_timeout)

        # audited modes (1 everywhere; ears 3/5/6): a PASSING submission must additionally
        # survive the adversarial counterexample audit — a mechanically
        # re-validated "real" ground-truth violation demotes the pass;
        # inconclusive/bad_test never do (infra noise is not a violation).
        if task.scored_on_audit and g.passed:
            from . import adversary
            adv = adversary.audit_product(iid, res.submission.patch or "",
                                          idir / "adversary", tag=run_id)
            g.adversary = adv
            if adv.get("category") == "real":
                g.passed = False
            g.note += (f"; adversary={adv.get('category')} "
                       f"({adv.get('detail', '')[:100]})")

        (idir / "grade").mkdir(exist_ok=True)
        (idir / "grade" / "result.json").write_text(json.dumps(g.as_dict(), indent=2) + "\n")

        # status first so per-instance metrics see the final fields
        st = _write_status(run_id, iid, state="done", submitted=res.submitted,
                           stop=res.stop, steps=res.steps, usage=res.usage,
                           passed=g.passed, resolved=g.resolved, verified=g.verified,
                           antifakery_ok=g.antifakery_ok, equivalent=g.equivalent,
                           spec_ok=g.spec_ok,
                           adversary_category=(g.adversary or {}).get("category"),
                           audit_clean=arep.clean, audit_flags=len(arep.flags),
                           note=g.note, ended_at=time.time(),
                           wall_s=round(time.time() - t0, 1))
        im = metrics.per_instance_metrics(res.trajectory, g.as_dict(), st,
                                          workdir=c.workdir)
        _write_status(run_id, iid, metrics=im)
        return {"instance_id": iid, "state": "done", "passed": g.passed,
                "resolved": g.resolved, "audit_clean": arep.clean,
                "verified_model": im.get("got_verified_model")}

    except CredentialsExpired as e:
        _write_status(run_id, iid, state="creds_expired", error=str(e), ended_at=time.time())
        return {"instance_id": iid, "state": "creds_expired"}
    except Exception as e:  # noqa: BLE001
        _write_status(run_id, iid, state="error", error=f"{type(e).__name__}: {e}",
                      traceback=traceback.format_exc()[-2000:], ended_at=time.time())
        return {"instance_id": iid, "state": "error", "error": str(e)}


def _select(run_id: str, instances: list[str], resume: bool) -> list[str]:
    if not resume:
        return instances
    todo = []
    for iid in instances:
        st = _read_status(run_id, iid)
        if st is None or st.get("state") in RESUMABLE:
            todo.append(iid)
    return todo


def write_summary(run_id: str, instances: list[str]) -> dict:
    rows = []
    for iid in instances:
        st = _read_status(run_id, iid) or {"instance_id": iid, "state": "missing"}
        rows.append(st)
    done = [r for r in rows if r.get("state") == "done"]
    cfg = {}
    cfg_p = _run_dir(run_id) / "config.json"
    if cfg_p.exists():
        try:
            cfg = json.loads(cfg_p.read_text())
        except json.JSONDecodeError:
            cfg = {}
    summ = {
        "run_id": run_id,
        "mode": cfg.get("mode"),
        "model": cfg.get("model"),
        "backend": cfg.get("backend"),
        "total": len(instances),
        "done": len(done),
        "passed": sum(1 for r in done if r.get("passed")),
        "resolved": sum(1 for r in done if r.get("resolved")),
        "audit_flagged": sum(1 for r in done if r.get("audit_clean") is False),
        # audited modes: adversarial counterexample audit tally (None elsewhere)
        "adversary_real": sum(1 for r in done
                              if r.get("adversary_category") == "real"),
        "adversary_inconclusive": sum(1 for r in done
                                      if r.get("adversary_category") == "inconclusive"),
        "creds_expired": sum(1 for r in rows if r.get("state") == "creds_expired"),
        "error": sum(1 for r in rows if r.get("state") == "error"),
        "pending": sum(1 for r in rows if r.get("state") in (None, "pending", "running")),
        "metrics": metrics.aggregate(rows),
        "instances": {r.get("instance_id", "?"): {k: r.get(k) for k in
                      ("state", "passed", "resolved", "verified", "equivalent",
                       "spec_ok", "antifakery_ok", "adversary_category",
                       "audit_clean", "audit_flags", "stop", "steps",
                       "wall_s", "metrics")}
                      for r in rows},
    }
    (_run_dir(run_id)).mkdir(parents=True, exist_ok=True)
    (_run_dir(run_id) / "summary.json").write_text(json.dumps(summ, indent=2) + "\n")
    return summ


def main() -> int:
    ap = argparse.ArgumentParser(description="resumable parallel eval driver")
    ap.add_argument("--backend", required=True, choices=sorted(BACKENDS),
                    help="which verification backend's bundles/verifier to evaluate against")
    ap.add_argument("--mode", type=int, required=True,
                    choices=[0, 1, 2, 3, 4, 5, 6, 7, 8],
                    help="0 baseline · 1 audited baseline · 2 end-to-end · "
                         "3 end-to-end scored on verify+equivalence · "
                         "4 localization · 5 verified-4 (localization + verifier, "
                         "scratch judge; ears = audited mode 4) · 6 spec-aided · "
                         "7 spec→verified · 8 spec generation (spec-quality "
                         "audit; N/A for ears). EARS audited pairs: 4/5, 7/6, "
                         "2/3 — all resolve-scored")
    ap.add_argument("--model", required=True, choices=sorted(MODEL_PRESETS))
    ap.add_argument("--judge-model", default="opus-4.8", choices=sorted(MODEL_PRESETS))
    ap.add_argument("--instances", nargs="*", default=[])
    ap.add_argument("--all", action="store_true",
                    help="run every instance in the frozen dataset (all 500); "
                         "combine with --frozen-list to run a frozen subset instead")
    ap.add_argument("--frozen-list", default=None, metavar="FILE",
                    help="with --all: read the instance set from FILE (one id per "
                         "line) instead of the full dataset, so a partial run is "
                         "comparable across models")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--instance-concurrency", type=int, default=4)
    ap.add_argument("--max-steps", type=int, default=None,
                    help=f"step budget per instance, SAME for all modes "
                         f"(default {DEFAULT_EVAL_MAX_STEPS})")
    ap.add_argument("--bash-timeout", type=int, default=120)
    ap.add_argument("--resolve-timeout", type=int, default=3600,
                    help="grading harness timeout per instance (s); a few suites "
                         "(e.g. scikit-learn) legitimately need >1800s")
    ap.add_argument("--include-hints", action="store_true")
    ap.add_argument("--nuclear-sanitize", action="store_true")
    ap.add_argument("--no-resume", action="store_true", help="re-run even finished instances")
    args = ap.parse_args()

    adapter = get_adapter(args.backend)
    # fail fast on unsupported combos (build_task would error per-instance)
    if args.backend == "ears" and args.mode == 8:
        print("mode 8 is not applicable for the ears backend", file=sys.stderr)
        return 2
    if args.all:
        instances = (frozen_instance_ids(Path(args.frozen_list)) if args.frozen_list
                     else all_instance_ids())
    else:
        instances = args.instances
    instances = list(dict.fromkeys(instances))   # dedupe, order-preserving
    if not instances:
        print("no instances (pass --instances ... or --all)", file=sys.stderr)
        return 2
    run_id = args.run_id or f"{args.backend}-m{args.mode}-{args.model}"
    rd = _run_dir(run_id)
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "config.json").write_text(json.dumps({
        "run_id": run_id, "backend": args.backend, "mode": args.mode, "model": args.model,
        "judge_model": args.judge_model, "instance_concurrency": args.instance_concurrency,
        "max_steps": args.max_steps, "include_hints": args.include_hints,
        "nuclear_sanitize": args.nuclear_sanitize, "n_instances": len(instances),
        "frozen_list": args.frozen_list,
    }, indent=2) + "\n")

    todo = _select(run_id, instances, resume=not args.no_resume)
    print(f"run {run_id}: {len(todo)}/{len(instances)} to run "
          f"(backend {args.backend}, mode {args.mode}, model {args.model}, "
          f"conc {args.instance_concurrency})")

    # ears never uses the equivalence/spec judge (resolve±audit scoring only)
    judge_key = (args.judge_model
                 if args.mode in (3, 5, 7, 8) and args.backend != "ears"
                 else None)
    lock = threading.Lock()
    done_n = 0

    def _task(iid):
        return run_one(adapter, run_id, iid, args.mode, args.model, judge_key,
                       args.max_steps, args.bash_timeout, args.resolve_timeout,
                       args.include_hints, args.nuclear_sanitize)

    with ThreadPoolExecutor(max_workers=args.instance_concurrency) as ex:
        futs = {ex.submit(_task, iid): iid for iid in todo}
        for fut in as_completed(futs):
            iid = futs[fut]
            try:
                r = fut.result()
            except Exception as e:  # noqa: BLE001
                r = {"instance_id": iid, "state": "error", "error": str(e)}
            with lock:
                done_n += 1
                tag = r.get("state")
                extra = ""
                if tag == "done":
                    extra = (f"passed={r.get('passed')} resolved={r.get('resolved')} "
                             f"audit_clean={r.get('audit_clean')}")
                print(f"  [{done_n}/{len(todo)}] {iid}: {tag} {extra}")
                write_summary(run_id, instances)   # checkpoint each completion
    summ = write_summary(run_id, instances)
    print("\n" + metrics.format_report(summ))
    print(f"\nfull metrics + per-instance breakdown: {_run_dir(run_id) / 'summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
