#!/usr/bin/env python
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Report: does a spec-correctness failure predict a downstream failure to resolve?

Thin CLI over `swebench_unified.eval.spec_impact` (which holds the joining and the
statistics, and documents the methodology). Reads only what is already on disk:
the blind re-audit written by `audit_scratch_specs.py` plus each run's grade/result.json.
It never calls a model, so it is safe to re-run while an audit is still going.

Runs are grouped into (backend, model, mode) cells discovered from each run's
config.json, and the seeds within a cell are treated as replicates. Cells are
reported separately, never pooled: the five properties are defined identically for
all three backends, but a ballot sees a Nagini contract vs a Lean theorem under a
per-backend judge prompt, so a cross-backend rate difference may reflect judge
calibration rather than spec quality.

    python scripts/eval/analyze_spec_impact.py
    python scripts/eval/analyze_spec_impact.py --out-dir experiments/reports/spec_impact
    python scripts/eval/analyze_spec_impact.py --runs nagini-m4-opus-4.8-s1 ... \
        --label "Opus 4.8 (nagini)"      # one explicit cell
"""
from __future__ import annotations

import argparse
import json
import statistics as stats
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from swebench_unified.eval import spec_impact as si  # noqa: E402
from swebench_unified.paths import EXPERIMENTS_ROOT  # noqa: E402
from swebench_unified.eval.grade import _SPEC_PROPERTIES  # noqa: E402

DEFAULT_OUT = EXPERIMENTS_ROOT / "reports" / "spec_impact"


def plot(label: str, agg: dict, out: Path):
    """Grouped bars, one group per property, one bar per split.

    matplotlib is imported lazily so the text report works without it (it is an
    optional `figures` extra, not a hard dependency of the package).
    """
    try:
        import matplotlib
        matplotlib.use("Agg")             # headless: no display
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("(no matplotlib/numpy: skipping figures; pip install -e '.[figures]')")
        return False

    # Unresolved FIRST so the eye lands on the failing population before its
    # resolved counterparts, which is the comparison the figure exists to make.
    order = [("unresolved", "#C62828", "Unresolved"),
             ("resolved", "#1E7A46", "Resolved"),
             ("overall", "#8E8E8E", "Overall")]
    order = [o for o in order if o[0] in agg["splits"]]
    props = list(_SPEC_PROPERTIES)
    x = np.arange(len(props))
    w = 0.26

    fig, ax = plt.subplots(figsize=(11.6, 5.4))
    for k, (split, color, leg) in enumerate(order):
        e = agg["splits"][split]
        mu = [e[p]["mean"] for p in props]
        sd = [e[p]["std"] for p in props]
        off = (k - (len(order) - 1) / 2) * w
        n = round(stats.mean(e["n_instances"]))
        ax.bar(x + off, mu, w, yerr=sd, capsize=4, color=color, alpha=0.88,
               edgecolor="white", linewidth=0.8,
               error_kw={"ecolor": "#333333", "lw": 1.2},
               label=f"{leg}  (n≈{n}/seed)", zorder=3)
        for xi, m, s in zip(x + off, mu, sd):
            ax.text(xi, m + s + 1.6, f"{m:.1f}\n±{s:.1f}", ha="center",
                    va="bottom", fontsize=7.6, color="#222222", linespacing=1.25,
                    zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels([si.NICE[p] for p in props], fontsize=10.5)
    ax.set_ylabel("specifications failing the property (%)", fontsize=10.5)
    # Headroom for the two-line value label ABOVE the error bar. Rates are already
    # percentages, so let the axis run past 100 rather than clipping the tallest
    # label (faithfulness sits in the 90s for unresolved instances).
    top = max(e[p]["mean"] + e[p]["std"]
              for e in agg["splits"].values() for p in props)
    ax.set_ylim(0, top + 14)
    ax.set_yticks(list(range(0, 101, 20)))
    n_seeds = max(e["n_seeds"] for e in agg["splits"].values())
    ax.set_title(f"{label}: specification-correctness failures vs downstream outcome"
                 f"   (mean ± std over {n_seeds} seed{'s' if n_seeds != 1 else ''})",
                 fontsize=12, pad=12)
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    ax.grid(axis="y", ls=":", lw=0.7, color="#BBBBBB", zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=170, facecolor="white")
    plt.close(fig)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="spec-correctness vs downstream outcome")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--runs", nargs="*", default=[],
                    help="treat these run ids as ONE cell's seeds (default: "
                         "auto-discover and group by backend/model/mode)")
    ap.add_argument("--label", default="", help="cell label, with --runs")
    ap.add_argument("--prefix", default="", help="only auto-discovered runs with this prefix")
    ap.add_argument("--no-figures", action="store_true", help="text report only")
    args = ap.parse_args()

    # (label, slug, seed run ids), one entry per cell
    if args.runs:
        cells = [(args.label or ", ".join(args.runs), "custom", args.runs)]
    else:
        cells = [(si.cell_label(k), si.cell_slug(k), runs)
                 for k, runs in si.cells(args.prefix).items()]
    cells.sort()

    if not cells:
        print(f"no audited runs under {si.AUDIT_ROOT}\n"
              f"run scripts/eval/audit_scratch_specs.py first", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    report, blob = [], {}
    for label, slug, cell_runs in cells:
        runs = sorted(cell_runs)
        agg = si.aggregate(runs)
        if not agg.get("splits"):
            print(f"(skip {label}: no decisive audits yet)")
            continue
        agg["runs"] = runs
        blob[label] = agg
        report.append(si.table(label, agg))
        if not args.no_figures:
            png = out_dir / f"m4_spec_impact_{slug}.png"
            if plot(label, agg, png):
                print(f"wrote {png}")
            else:
                args.no_figures = True     # matplotlib missing: stop retrying

    if not blob:
        print("no cell had a decisive audit yet", file=sys.stderr)
        return 1

    (out_dir / "m4_spec_impact.json").write_text(json.dumps(blob, indent=2) + "\n")
    txt = "\n\n".join(report)
    (out_dir / "m4_spec_impact.txt").write_text(txt + "\n")
    print(f"wrote {out_dir / 'm4_spec_impact.json'} and .txt\n")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
