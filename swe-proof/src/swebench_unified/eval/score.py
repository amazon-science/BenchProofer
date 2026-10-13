# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Score mode — mechanical consumer scorer: the headline `verified => resolved`
test over predictions of (<solution file>, patch.diff) per instance.

  resolved — official harness on the candidate's patch.diff (real oracle)
  verified — frozen-spec audit + backend check + hygiene + G-CONF re-run on the
             candidate's own refinement. (G-AX carries over from the frozen
             bundle — frozen spec the consumer cannot edit; G-CONF IS re-run
             because the candidate's R/I legs are new.)

The candidate must NOT alter the frozen spec region: `verified` requires
same_spec(frozen, candidate) under the unified markers.

Usage (the oracle legs need docker; how this account reaches the daemon is probed,
and `SBU_DOCKER_CMD` overrides the answer — see docs/reproducing.md):
    python -m swebench_unified.eval \
        --backend lean --predictions <preds_dir>/ --output results-eval/
    python -m swebench_unified.eval --backend lean --summarize results-eval/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ..docker_exec import ensure_image, run_in_container
from ..backends.registry import GATED_BACKENDS
from ..harness import run_resolve
from ..markers import same_spec
from ..paths import DATASET_JSONL, RUN_PREFIX, bundle_dir
from .adapter import EvalAdapter, get_adapter


def _frozen_row(instance_id: str) -> dict | None:
    with DATASET_JSONL.open() as fh:
        for line in fh:
            if f'"{instance_id}"' in line:
                row = json.loads(line)
                if row.get("instance_id") == instance_id:
                    return row
    return None


def _hygiene_ok(adapter: EvalAdapter, instance_id: str, pred_dir: Path) -> tuple[bool, str]:
    """Hygiene on the candidate. Preferred: the construction-side G-HYGIENE
    gate (imported lazily, so scoring still runs where the construction gates
    are not installed); if unavailable, degrade to the strictly weaker
    eval-side anti-fakery hygiene with a warning, flagged in the note."""
    try:
        from ..gates import hygiene as g_hygiene
        from ..gates.base import Bundle

        class _PredBundle(Bundle):
            """Bundle whose constructed-artifact root is the PREDICTION dir
            (the candidate's files), not tasks/<id>/<backend>/."""
            @property
            def root(self):  # type: ignore[override]
                return pred_dir
    except (ImportError, AttributeError) as e:
        # degrade ONLY when the gate is genuinely unavailable — never to mask
        # a real hygiene failure
        import sys
        print(f"WARNING: G-HYGIENE gate unavailable ({type(e).__name__}: {e}); "
              f"falling back to eval-side anti-fakery hygiene (weaker check)",
              file=sys.stderr)
        src_p = pred_dir / adapter.solution_filename
        src = src_p.read_text() if src_p.exists() else None
        ok, note = adapter.antifakery(src)
        return ok, f"eval-side hygiene fallback ({note}); construction gate unavailable"
    # gate importable: a runtime error while RUNNING it fails closed rather
    # than substituting the weaker check (source-equivalent scoring)
    try:
        r = g_hygiene.run(_PredBundle(instance_id, adapter.backend))
        return r.ok, f"G-HYGIENE: {r.detail}"
    except Exception as e:  # noqa: BLE001
        return False, f"G-HYGIENE errored ({type(e).__name__}: {e}) — fail closed"


def _conf_ok(adapter: EvalAdapter, instance_id: str, pred_dir: Path,
             cand_patch: Path, frozen_meta: dict, container_timeout: int) -> tuple[bool, dict]:
    """G-CONF re-run on the candidate's own (impl, patch.diff) refinement.

    Runs the prediction's conformance_check.py directly rather than through the
    G-CONF gate: the gate judges a constructed bundle, reading that bundle's
    shadow and applying its gold patch.diff, while here both the shadow and the
    patch under test are the candidate's. A prediction with no
    conformance_check.py fails conf, with a note."""
    extra: dict = {}
    if frozen_meta.get("conf_skip"):
        extra["conf_skipped"] = True
        return True, extra  # skip counts as passing (residual trust flagged)

    cand_conf = pred_dir / "conformance_check.py"
    if not cand_conf.exists():
        extra["note"] = "no conformance_check.py in prediction"
        return False, extra
    cr = run_in_container(instance_id, str(pred_dir.resolve()),
                          "conformance_check.py",
                          gold_patch_path=str(cand_patch.resolve()),
                          apply_gold=True, timeout=container_timeout,
                          need_hypothesis=True)
    return cr.ok, extra


def evaluate_one(adapter: EvalAdapter, instance_id: str, pred_dir: Path,
                 verify_timeout: int, resolve_timeout: int,
                 container_timeout: int) -> dict:
    """Score one prediction (candidate solution + patch.diff [+ refinement.md
    + conformance_check.py])."""
    res = {"instance_id": instance_id, "resolved": False, "verified": False,
           "verified_breakdown": {}, "note": ""}
    frozen = bundle_dir(instance_id, adapter.backend.name)
    cand_sol = pred_dir / adapter.solution_filename
    cand_patch = pred_dir / "patch.diff"
    if not cand_sol.exists() or not cand_patch.exists():
        res["note"] = f"prediction missing {adapter.solution_filename} or patch.diff"
        return res

    # --- resolved (real oracle) ---
    err = ensure_image(instance_id)
    if err:
        res["note"] = err
        return res
    rr = run_resolve(instance_id, cand_patch.read_text(),
                     run_id=f"eval-{RUN_PREFIX}-{instance_id}", timeout=resolve_timeout,
                     retries=2)
    res["resolved"] = bool(rr.resolved)
    res["resolve_attempts"] = rr.attempts
    res["resolve_flaky"] = rr.flaky

    # --- verified ---
    bd = res["verified_breakdown"]
    # (a) frozen spec region unchanged (unified markers)
    frozen_sol = frozen / adapter.solution_filename
    bd["same_spec"] = frozen_sol.exists() and same_spec(
        frozen_sol.read_text(), cand_sol.read_text(), adapter.backend.language)
    # (b) candidate solution passes the backend checker
    try:
        fe = adapter.float_encoding(instance_id)
    except json.JSONDecodeError:
        fe = None
    if adapter.supports_float_encoding and fe:
        bd["check"] = adapter.backend.check(cand_sol, timeout=verify_timeout,
                                            float_encoding=fe).success
    else:
        bd["check"] = adapter.backend.check(cand_sol, timeout=verify_timeout).success
    # (c) hygiene on candidate (gate if available, eval-side fallback otherwise)
    bd["hygiene"], hygiene_note = _hygiene_ok(adapter, instance_id, pred_dir)
    if hygiene_note:
        bd["hygiene_note"] = hygiene_note
    # (d) G-CONF re-run. A corrupt frozen meta degrades to {} (source parity)
    # so conf runs rather than being skipped.
    try:
        frozen_meta = adapter.bundle_meta(instance_id)
    except json.JSONDecodeError:
        frozen_meta = {}
    bd["conf"], conf_extra = _conf_ok(adapter, instance_id, pred_dir, cand_patch,
                                      frozen_meta, container_timeout)
    bd.update(conf_extra)

    res["verified"] = all(bd.get(k, False) for k in
                          ("same_spec", "check", "hygiene", "conf"))
    return res


def summarize_eval(out_dir: Path) -> dict:
    rows = [json.loads(p.read_text()) for p in sorted(out_dir.glob("*/eval.json"))]
    n = len(rows)
    resolved = sum(r["resolved"] for r in rows)
    verified = sum(r["verified"] for r in rows)
    both = sum(r["resolved"] and r["verified"] for r in rows)
    v_not_r = [r["instance_id"] for r in rows if r["verified"] and not r["resolved"]]
    p_r_given_v = (both / verified) if verified else float("nan")
    p_v_given_r = (both / resolved) if resolved else float("nan")
    summary = {
        "n": n,
        "resolved_count": resolved,
        "verified_count": verified,
        "resolved_and_verified": both,
        "P_resolved_given_verified": p_r_given_v,
        "P_verified_given_resolved": p_v_given_r,
        "verified_and_not_resolved": v_not_r,  # the soundness counterexamples
    }
    print(f"\n=== consumer eval ({n} predictions) ===")
    print(f"  resolved:              {resolved}/{n}")
    print(f"  verified:              {verified}/{n}")
    print(f"  resolved AND verified: {both}/{n}  (headline)")
    print(f"  P(resolved|verified):  {p_r_given_v:.4f}  (soundness probe; target ~1.0)")
    print(f"  P(verified|resolved):  {p_v_given_r:.4f}  (spec tightness)")
    if v_not_r:
        print(f"  !! verified AND NOT resolved ({len(v_not_r)}): {v_not_r}")
        print("     ^ strongest possible test FAILURE — falsifies verify=>resolved; audit each.")
    else:
        print("  verified ∧ ¬resolved = EMPTY  (verify => resolved holds on this set)")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(
        description="mechanical consumer scorer: verified => resolved over a predictions dir")
    ap.add_argument("--backend", choices=list(GATED_BACKENDS),
                    help="required unless --summarize")
    ap.add_argument("--predictions",
                    help="dir with <id>/<solution file> + patch.diff per instance")
    ap.add_argument("--dataset", default=str(DATASET_JSONL))
    ap.add_argument("--instances", help="file or process-sub with ids to score")
    ap.add_argument("--output", default="results-eval")
    ap.add_argument("--summarize", help="summarize an existing output dir and exit")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--verify-timeout", type=int, default=300)
    ap.add_argument("--resolve-timeout", type=int, default=3600)
    ap.add_argument("--container-timeout", type=int, default=1800)
    args = ap.parse_args()

    if args.summarize:
        summarize_eval(Path(args.summarize))
        return 0

    if not args.backend:
        ap.error("--backend is required (unless --summarize)")
    if not args.predictions:
        ap.error("--predictions is required (unless --summarize)")
    adapter = get_adapter(args.backend)
    preds = Path(args.predictions)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.instances:
        ids = [ln.strip() for ln in Path(args.instances).read_text().splitlines()
               if ln.strip()]
    else:
        ids = sorted(p.name for p in preds.iterdir() if p.is_dir())

    for iid in ids:
        r = evaluate_one(adapter, iid, preds / iid, args.verify_timeout,
                         args.resolve_timeout, args.container_timeout)
        d = out_dir / iid
        d.mkdir(parents=True, exist_ok=True)
        (d / "eval.json").write_text(json.dumps(r, indent=2))
        print(f"[{iid}] resolved={r['resolved']} verified={r['verified']} {r.get('note','')}")

    summarize_eval(out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
