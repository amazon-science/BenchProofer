# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Print / recompute eval metrics from saved runs, plus a cross-mode ablation
table when runs of the same model differ by mode.

  python -m swebench_unified.eval.report <run_id> [<run_id> ...]

Never re-runs anything; only reads experiments/eval/<run_id>/.
"""
from __future__ import annotations

import argparse
import json
import sys

from ..paths import EXPERIMENTS_ROOT
from . import metrics

EVAL_ROOT = EXPERIMENTS_ROOT / "eval"


def _load_run(run_id: str) -> dict:
    rd = EVAL_ROOT / run_id
    cfg = {}
    if (rd / "config.json").exists():
        cfg = json.loads((rd / "config.json").read_text())
    rows = []
    for d in sorted(rd.iterdir()):
        sp = d / "status.json"
        if d.is_dir() and sp.exists():
            st = json.loads(sp.read_text())
            # backfill metrics for old runs that predate metrics.py
            if st.get("state") == "done" and "metrics" not in st:
                tp, gp = d / "trajectory.jsonl", d / "grade" / "result.json"
                traj = [json.loads(ln) for ln in tp.open()] if tp.exists() else []
                g = json.loads(gp.read_text()) if gp.exists() else {}
                st["metrics"] = metrics.per_instance_metrics(traj, g, st)
            rows.append(st)
    summ = {
        "run_id": run_id, "mode": cfg.get("mode"), "model": cfg.get("model"),
        "backend": cfg.get("backend"),
        "total": len(rows), "done": sum(1 for r in rows if r.get("state") == "done"),
        "passed": sum(1 for r in rows if r.get("passed")),
        "resolved": sum(1 for r in rows if r.get("resolved")),
        "error": sum(1 for r in rows if r.get("state") == "error"),
        "creds_expired": sum(1 for r in rows if r.get("state") == "creds_expired"),
        "audit_flagged": sum(1 for r in rows if r.get("state") == "done"
                             and r.get("audit_clean") is False),
        "metrics": metrics.aggregate(rows),
        "_rows": rows,
    }
    return summ


def _ablation(summaries: list[dict]) -> str:
    """Cross-mode ablation table when runs share a model but differ by mode."""
    by_mode = {s["mode"]: s for s in summaries if s.get("mode") is not None}
    if len(by_mode) < 2:
        return ""
    L = ["", "CROSS-MODE ABLATION (resolve rate; same model)"]
    def rr(m):
        s = by_mode.get(m)
        return s["metrics"].get("resolve_rate") if s else None
    def pct(x):
        return f"{x*100:.1f}%" if isinstance(x, (int, float)) else "n/a"
    for m, label in [(0, "mode 0  baseline (canonical SWE-bench)"),
                     (4, "mode 4  localization-only baseline"),
                     (6, "mode 6  + spec + verifier"),
                     (2, "mode 2  end-to-end (construct+verify)"),
                     (3, "mode 3  end-to-end (pass=verify∧resolve∧equiv)"),
                     (7, "mode 7  spec→verified (pass=verify∧resolve∧equiv)"),
                     (8, "mode 8  spec-generation (pass=spec audit)")]:
        if m in by_mode:
            s = by_mode[m]
            if m == 8:
                # not resolve-scored; show the spec-audit pass rate
                L.append(f"    {label:46s} spec-pass {pct(s['metrics'].get('pass_rate'))}")
                continue
            # pass < resolve only for the equivalence-scored modes (7, 3)
            tail = f"   [pass {pct(s['metrics'].get('pass_rate'))}]" if m in (3, 7) else ""
            L.append(f"    {label:46s} resolve {pct(rr(m))}{tail}")
    r_loc, r_spec, r_e2e = rr(4), rr(6), rr(2)
    if r_loc is not None and r_spec is not None:
        L.append(f"    => spec+verifier benefit (mode6 − mode4): {(r_spec-r_loc)*100:+.1f} pts")
    if r_loc is not None and r_e2e is not None:
        L.append(f"    => localization benefit (mode4 − mode2): {(r_loc-r_e2e)*100:+.1f} pts")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="print/recompute eval metrics from saved runs")
    ap.add_argument("run_ids", nargs="+")
    ap.add_argument("--write", action="store_true",
                    help="also (re)write each run's summary.json with recomputed metrics")
    args = ap.parse_args()
    summaries = []
    for rid in args.run_ids:
        if not (EVAL_ROOT / rid).is_dir():
            print(f"(no such run: {rid})", file=sys.stderr)
            continue
        s = _load_run(rid)
        summaries.append(s)
        print(metrics.format_report(s))
        print()
        if args.write:
            s2 = {k: v for k, v in s.items() if k != "_rows"}
            (EVAL_ROOT / rid / "summary.json").write_text(json.dumps(s2, indent=2) + "\n")
    abl = _ablation(summaries)
    if abl:
        print(abl)
    return 0


if __name__ == "__main__":
    sys.exit(main())
