# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Cross-cell checks: the single site loads every BENCHMARK x BACKEND cell.
The board's green is STRICTER than scripts/green_check.py (every gate must be
RECORDED, not just non-failing) — so board-green must be a SUBSET of
green_check-green, never a superset."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import CELLS, FULL_BM, FULL_IID, corpus_size

REPO = Path(__file__).resolve().parents[2]

_PROBE = '''
import sys, json
bm, bk, iid = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, "viz")
from backend import data, settings
t = data.summary_table(bm, bk)
green_ids = [r["instance_id"] for r in t if r["green"]]
print(json.dumps({
    "n": len(t),
    "green": sum(1 for r in t if r["green"]),
    "green_ids": green_ids,
    "model_file": settings.model_file(bk),
    "has_model": data.read_bundle_file(bm, bk, iid, settings.model_file(bk)) is not None,
    "prepatch": data.list_prepatch(bm, bk, iid),
    "prepatch_diffs": bool(data.prepatch_diffs(bm, bk, iid)),
}))
'''

def _green_check(bench_dir: str, sbu_benchmark: str, backend: str) -> set:
    out = subprocess.run(
        [sys.executable, "scripts/green_check.py",
         "--benchmark-dir", bench_dir, "--backend", backend],
        env=dict(os.environ, SBU_BENCHMARK=sbu_benchmark),
        capture_output=True, text=True, cwd=REPO, check=True)
    return {ln.split("\t")[1] for ln in out.stdout.splitlines() if ln.startswith("GREEN")}


def _probe(bm: str, backend: str, iid: str = FULL_IID) -> dict:
    out = subprocess.run(
        [sys.executable, "-c", _PROBE, bm, backend, iid],
        env=dict(os.environ, VIZ_AGENT_ENABLED="0"),
        capture_output=True, text=True, cwd=REPO, check=True)
    return json.loads(out.stdout)


@pytest.mark.parametrize("backend", ["nagini", "velvet", "lean"])
def test_backend_board_reads_a_cells_artifacts(backend):
    """Each backend's loaders resolve a real bundle's files under its own naming
    convention (model / prepatch stem / extension all differ per backend)."""
    d = _probe(FULL_BM, backend)
    assert d["n"] == corpus_size(FULL_BM)
    assert d["has_model"], f"{backend}: model file {d['model_file']} not readable"
    assert d["prepatch"] and d["prepatch_diffs"]


@pytest.mark.parametrize("backend", ["nagini", "velvet", "lean"])
def test_strict_green_is_not_vacuous(backend):
    """The classifier must be able to call something green.

    Checked across the whole matrix rather than per benchmark: a benchmark whose
    falsification batteries are not constructed yet has every cell legitimately
    non-green (a `pbt_missing_manifest` skip is not a verdict), so an empty board
    there is a fact about the corpus, not a broken classifier. Asserting
    non-emptiness per cell would make this test fail for corpus progress, which
    the green counts already report and which no code change can fix.
    """
    green = set()
    for bm, _dir, _sbu in CELLS:
        green |= set(_probe(bm, backend)["green_ids"])
    assert green, f"{backend}: no cell in the matrix is strict-green — classifier broken?"


@pytest.mark.parametrize("bm,bench_dir,sbu", CELLS)
@pytest.mark.parametrize("backend", ["nagini", "velvet", "lean"])
def test_every_cell_loads_and_green_is_a_subset(backend, bm, bench_dir, sbu):
    """Every matrix cell loads its own dataset, and each board's strict green
    stays a subset of scripts/green_check.py for THAT benchmark dir."""
    d = _probe(bm, backend)
    n = corpus_size(bm)
    assert d["n"] == n, f"{bm}/{backend}: expected {n} instances, got {d['n']}"
    gc = _green_check(bench_dir, sbu, backend)
    board = set(d["green_ids"])
    assert board <= gc, \
        f"{bm}/{backend}: board-green not a subset of green_check: {sorted(board - gc)[:3]}"
