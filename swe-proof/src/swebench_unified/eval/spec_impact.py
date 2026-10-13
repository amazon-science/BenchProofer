# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Does a specification-correctness failure predict a downstream failure to resolve?

Mode 8 scores specs in isolation and finds faithfulness to be the bottleneck. This
module joins that same five-property audit (re-run over mode-3 artifacts by
`scripts/eval/audit_scratch_specs.py`, blind to the outcome and to the agent's patch)
against each mode-3 instance's SWE-bench result, and reports the per-property
failure rate split by whether the instance resolved.

The split variable is `resolved` (the SWE-bench test verdict), because the question
is about downstream task success. `passed` (verify AND resolve AND equivalent) is
reported alongside it, but it is NOT the headline: it embeds the formal verdict, so
conditioning on it would partly correlate the audit with itself.

Per-property "%fail" is over DECISIVE ballots, majority rule — identical to the
mode-8 headline (`grade.grade_spec`), so the numbers are comparable to the
spec-synthesis table. Instances whose ballots all abstained on infrastructure
contribute to no split.

Each seed is one independent replicate: the rate is computed WITHIN a seed and
reported as mean +/- population std ACROSS seeds, so the error bar is seed-to-seed
variation rather than binomial noise pooled over a mixed population.

Backends are kept SEPARATE, never pooled. The five properties are defined
identically for all three, but a ballot sees a Nagini contract vs a Lean theorem
under a per-backend judge prompt, so a cross-backend rate difference may reflect
judge calibration rather than spec quality.

Read-only: consumes `experiments/eval/<run_id>/` + `experiments/eval/m4_spec_audit/
<run_id>/` and never re-runs a model.
"""
from __future__ import annotations

import json
import statistics as stats

from ..paths import EXPERIMENTS_ROOT
from .grade import _SPEC_PROPERTIES

EVAL_ROOT = EXPERIMENTS_ROOT / "eval"
AUDIT_ROOT = EVAL_ROOT / "m4_spec_audit"

SPLITS = ("resolved", "unresolved", "overall")
# spec-level rollup key; leading underscore keeps it out of the per-property loop
ANY_KEY = "_any"
NICE = {"axioms_sound": "Axiom\nsoundness", "admissible": "Admissibility",
        "sound": "Soundness", "complete": "Completeness", "faithful": "Faithfulness"}


def run_config(run_id: str) -> dict:
    """A run's config.json (backend, mode, model, benchmark, ...).

    Recorded per run by eval/run.py, so the analysis never has to parse a run-id
    naming convention. Empty dict when the run predates config.json or is unreadable.
    """
    p = EVAL_ROOT / run_id / "config.json"
    if not p.exists():
        return {}
    try:
        cfg = json.loads(p.read_text())
    except json.JSONDecodeError:
        return {}
    return cfg if isinstance(cfg, dict) else {}


def run_backend(run_id: str) -> str | None:
    """The backend a run was produced with. None if unrecorded."""
    return run_config(run_id).get("backend")


def audited_runs(prefix: str = "") -> list[str]:
    """Run ids that have at least one audit ballot on disk."""
    if not AUDIT_ROOT.is_dir():
        return []
    out = []
    for d in sorted(AUDIT_ROOT.iterdir()):
        if d.is_dir() and d.name.startswith(prefix) and any(d.glob("*.json")):
            out.append(d.name)
    return out


def cells(prefix: str = "") -> dict[tuple[str, str, int | None], list[str]]:
    """Group audited runs into (backend, model, mode) cells; seeds are the values.

    Discovered from each run's config.json rather than a hardcoded model list: with
    three backends x N models x M seeds, a literal table goes stale the first time a
    seed is added. Runs with no config.json land in an ("?", "?", None) cell so they
    are visible rather than silently dropped.
    """
    out: dict[tuple[str, str, int | None], list[str]] = {}
    for run_id in audited_runs(prefix):
        cfg = run_config(run_id)
        key = (cfg.get("backend") or "?", cfg.get("model") or "?", cfg.get("mode"))
        out.setdefault(key, []).append(run_id)
    return out


def cell_label(key: tuple[str, str, int | None]) -> str:
    """Human label for a cell key, e.g. 'nagini / opus-4.8 / mode 3'."""
    backend, model, mode = key
    return f"{backend} / {model} / mode {mode if mode is not None else '?'}"


def cell_slug(key: tuple[str, str, int | None]) -> str:
    """Filename-safe slug for a cell key, e.g. 'nagini-opus-4.8-m4'."""
    backend, model, mode = key
    return f"{backend}-{model}-m{mode if mode is not None else 'x'}".replace("/", "_")


def load_seed(run_id: str) -> list[dict]:
    """One seed's instances joined: audit verdict + downstream SWE-bench outcome."""
    rows = []
    for f in sorted((AUDIT_ROOT / run_id).glob("*.json")):
        try:
            audit = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue                      # half-written ballot from a killed run
        iid = audit.get("instance_id") or f.stem
        decisive = [v for v in audit.get("votes", []) if not v.get("parse_error")]
        if not decisive:
            continue                      # total infra abstention: no verdict to use
        gres = EVAL_ROOT / run_id / iid / "grade" / "result.json"
        if not gres.exists():
            continue
        try:
            g = json.loads(gres.read_text())
        except json.JSONDecodeError:
            continue
        n = len(decisive)
        # majority of decisive ballots failed the property (mode-8 headline rule)
        fails = {p: sum(1 for v in decisive if not v.get(p, False)) > n / 2
                 for p in _SPEC_PROPERTIES}
        rows.append({"instance_id": iid, "resolved": bool(g.get("resolved")),
                     "passed": bool(g.get("passed")), "spec_ok": audit.get("spec_ok"),
                     "n_decisive": n, "fails": fails})
    return rows


def rates(rows: list[dict], split: str) -> dict | None:
    """%fail per property (plus spec-level %fail) for one split of one seed."""
    if split == "resolved":
        sub = [r for r in rows if r["resolved"]]
    elif split == "unresolved":
        sub = [r for r in rows if not r["resolved"]]
    else:
        sub = rows
    if not sub:
        return None
    out = {p: 100.0 * sum(1 for r in sub if r["fails"][p]) / len(sub)
           for p in _SPEC_PROPERTIES}
    out[ANY_KEY] = 100.0 * sum(1 for r in sub if r["spec_ok"] is False) / len(sub)
    out["_n"] = len(sub)
    return out


def aggregate(run_ids: list[str]) -> dict:
    """Per-seed rates -> mean/std across seeds, per split.

    `run_ids` are replicates of ONE (model, backend) cell; each contributes one
    within-seed rate, so the std is seed-to-seed variation.
    """
    seeds = {r: load_seed(r) for r in run_ids}
    seeds = {r: v for r, v in seeds.items() if v}
    agg: dict = {"seeds": {r: len(v) for r, v in seeds.items()}, "splits": {}}
    if not seeds:
        return agg
    for split in SPLITS:
        per_seed = [rates(v, split) for v in seeds.values()]
        per_seed = [p for p in per_seed if p]
        if not per_seed:
            continue
        entry: dict = {"n_seeds": len(per_seed),
                       "n_instances": [p["_n"] for p in per_seed]}
        for key in list(_SPEC_PROPERTIES) + [ANY_KEY]:
            vals = [p[key] for p in per_seed]
            entry[key] = {"mean": stats.mean(vals),
                          "std": stats.pstdev(vals) if len(vals) > 1 else 0.0,
                          "per_seed": vals}
        agg["splits"][split] = entry
    # resolve rate itself, for context
    rr = [100.0 * sum(1 for r in v if r["resolved"]) / len(v) for v in seeds.values()]
    agg["resolve_rate"] = {"mean": stats.mean(rr),
                           "std": stats.pstdev(rr) if len(rr) > 1 else 0.0}
    return agg


def gap(agg: dict, prop: str) -> float | None:
    """unresolved %fail - resolved %fail for one property.

    The effect size the experiment exists to measure: positive means specs behind
    unresolved instances fail the property more often. None when either split is
    absent (e.g. a seed where everything resolved).
    """
    s = agg.get("splits", {})
    if "unresolved" not in s or "resolved" not in s:
        return None
    return s["unresolved"][prop]["mean"] - s["resolved"][prop]["mean"]


def table(label: str, agg: dict) -> str:
    """Fixed-width per-property table for one (model, backend) cell."""
    splits = [s for s in SPLITS if s in agg.get("splits", {})]
    L = [f"### {label}",
         (f"resolve rate: {agg['resolve_rate']['mean']:.1f}% "
          f"± {agg['resolve_rate']['std']:.1f}   "
          f"(audited instances/seed: {list(agg['seeds'].values())})"),
         "",
         f"{'property':<16}" + "".join(f"{s:>22}" for s in splits) + f"{'gap':>10}",
         "-" * (16 + 22 * len(splits) + 10)]
    for p in list(_SPEC_PROPERTIES) + [ANY_KEY]:
        name = "SPEC FAILS (any)" if p == ANY_KEY else p
        row = f"{name:<16}"
        for s in splits:
            e = agg["splits"][s][p]
            row += f"{e['mean']:>15.1f} ±{e['std']:<5.1f}"
        d = gap(agg, p)
        row += f"{d:>+10.1f}" if d is not None else f"{'n/a':>10}"
        L.append(row)
    return "\n".join(L)
