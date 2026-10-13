#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Import every bundle's `properties.py` and report the ones that cannot load.

A property battery pins the spec by surgery on frozen anchor text: it asserts, at
import time, that each anchor substring still occurs in the shipped solution.
When a spec repair moves that text and the anchors are not re-synced the import
raises, and then the whole battery is dead -- G-PBT reaches no verdict, every
reject case it would have built is unconstructible, and the cell cannot go green
however good the spec is.

This needs its own sweep rather than a scan of recorded G-PBT statuses, because a
gate stamp is a measurement from a point in time and nothing demotes it when the
spec later moves: a bundle can carry a passing G-PBT over a battery that no
longer imports. It is cheap enough to be a release check, one subprocess import
per bundle.

Each battery is imported in its OWN subprocess. In-process imports would share a
module namespace across files that all define the same top-level names, and a
battery may run arbitrary code at import, so one bad bundle could take down the
sweep or silently poison a later one.

Exit status: 0 if every battery imports, 1 if any failed, 2 on a usage error.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from swebench_unified.backends.registry import GATED_BACKENDS  # noqa: E402
from swebench_unified.corpus_root import default_benchmark_dir  # noqa: E402

# Imports only, so this is I/O bound rather than CPU bound and a short cap is
# generous. A battery that needs longer than this to IMPORT is itself the defect.
IMPORT_TIMEOUT_S = 300


def import_one(bundle: Path, python: str, bench: Path) -> tuple[bool, str]:
    """`(imported, one-line detail)` for one battery, in a fresh interpreter."""
    props = bundle / "properties.py"
    code = (
        "import importlib.util, pathlib\n"
        "p = pathlib.Path(__import__('sys').argv[1])\n"
        "s = importlib.util.spec_from_file_location('battery_under_test', p)\n"
        "m = importlib.util.module_from_spec(s)\n"
        "s.loader.exec_module(m)\n"
        "print(len(getattr(m, 'SPEC_TESTS', []) or []))\n"
    )
    # cwd is the repo root and SBU_BENCHMARK_DIR the ABSOLUTE resolved
    # --benchmark-dir: with a relative value and cwd inside the cell, the bundle
    # path doubles and every battery fails with a bogus FileNotFoundError. It is
    # the caller's corpus and not a fixed one, so that a battery which resolves
    # through the variable measures the tree this run was pointed at. No battery
    # shipped today reads it, which is why getting it wrong would be silent.
    #
    # SBU_BENCHMARK is inherited and never defaulted here: `benchmarks.py` owns
    # that default, and a checker carrying its own copy is how a tool ends up
    # disagreeing with the pipeline it checks.
    env = dict(os.environ,
               SBU_BENCHMARK_DIR=str(bench),
               PYTHONDONTWRITEBYTECODE="1")
    try:
        r = subprocess.run([python, "-c", code, str(props)],
                           cwd=ROOT, env=env, capture_output=True,
                           text=True, timeout=IMPORT_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return False, f"import exceeded {IMPORT_TIMEOUT_S}s"
    if r.returncode == 0:
        return True, f"SPEC_TESTS={r.stdout.strip()}"
    tail = [ln.strip() for ln in (r.stderr or "").strip().splitlines() if ln.strip()]
    return False, " | ".join(t[:200] for t in tail[-3:]) or "no stderr"


def recorded_pbt(bundle: Path) -> tuple[str, str]:
    try:
        meta = json.loads((bundle / "meta.json").read_text())
    except Exception:
        return "?", ""
    g = (meta.get("gates") or {}).get("G-PBT")
    if not isinstance(g, dict):
        return "absent", ""
    return str(g.get("status")), str(g.get("checked_at") or "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--benchmark-dir", default=default_benchmark_dir())
    ap.add_argument("--backend", action="append", default=[],
                    choices=list(GATED_BACKENDS),
                    help="restrict to these backends")
    ap.add_argument("--cells", default="",
                    help="TSV of '<instance_id>\\t<backend>' to restrict to")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    bench = ((ROOT / a.benchmark_dir) if not os.path.isabs(a.benchmark_dir)
             else Path(a.benchmark_dir)).resolve()
    if not bench.is_dir():
        print(f"no such benchmark dir: {bench}", file=sys.stderr)
        return 2
    backends = tuple(a.backend) or GATED_BACKENDS

    only: set[tuple[str, str]] | None = None
    if a.cells:
        only = set()
        for ln in Path(a.cells).read_text().splitlines():
            parts = ln.split()
            if len(parts) >= 2:
                only.add((parts[0], parts[1]))

    cells = []
    for d in sorted(bench.iterdir()):
        if not d.is_dir():
            continue
        for be in backends:
            b = d / be
            if not (b / "properties.py").is_file():
                continue
            if only is not None and (d.name, be) not in only:
                continue
            cells.append((d.name, be, b))
    if not cells:
        print("no cells with a properties.py matched", file=sys.stderr)
        return 2
    print(f"# {len(cells)} battery(ies), jobs={a.jobs}", flush=True)

    def work(item):
        iid, be, b = item
        ok, detail = import_one(b, a.python, bench)
        st, at = recorded_pbt(b)
        return {"instance_id": iid, "backend": be, "imports": ok,
                "detail": detail, "recorded_g_pbt": st, "checked_at": at}

    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        rows = list(ex.map(work, cells))

    bad = [r for r in rows if not r["imports"]]
    # The subset that matters most: the battery is broken AND the recorded gate
    # says pass, so nothing in the board is reporting the problem.
    silent = [r for r in bad if r["recorded_g_pbt"] == "pass"]

    for r in bad:
        flag = "STALE-PASS" if r["recorded_g_pbt"] == "pass" else \
            f"G-PBT={r['recorded_g_pbt']}"
        print(f"FAIL {r['instance_id']}/{r['backend']}  [{flag}]\n"
              f"     {r['detail']}")
    print(f"\n# ok={len(rows) - len(bad)} broken={len(bad)} "
          f"silently-broken={len(silent)}")
    if silent:
        print("# silently broken batteries carry a passing G-PBT stamp and are "
              "invisible to the board; they must be re-stamped after repair:")
        for r in silent:
            print(f"#   {r['instance_id']}\t{r['backend']}  "
                  f"(stamped {r['checked_at']})")
    if a.out:
        Path(a.out).write_text(json.dumps(rows, indent=1))
        print(f"# report -> {a.out}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
