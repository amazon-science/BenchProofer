#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-6992 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — `computeNameSets` (Solution.lean's deep model of the changed
              `Dataset.reset_index` name-set bookkeeping) transliterated to
              Python.  Its A-tagged input — the index footprint `{dim} ∪ levels`
              produced by `Indexes.get_all_coords` — is taken from the REAL index
              object (the A leg stays with G-AX); everything else is the R/I
              bookkeeping.
  * ORACLE  — `patch.diff`'s behaviour: the patched `Dataset.reset_index`
              applied at base_commit (gold patch git-applied in-container by the
              gate runner), observed as the resulting Dataset's three name-sets
              `(set(_variables), set(_coord_names), set(_indexes))`.

The Lean carriers are `List String`; the repo carriers are sets / dict-keysets
(`_coord_names` is a `set`, `_variables`/`_indexes` are dict keysets — mapping.md
§2), so the faithful bridge compares as SETS. They must agree on every input.
Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), `xarray`/`pandas`/
`numpy` + stdlib only. Fuzz seed pinned (mapping.md §5) for a deterministic
verdict. Scope: a single index group per dataset (one multi-/single index), the
shape the issue's MVCE and the F2P `reset_index` tests exercise; the structural
rule the bundle models is per-index.
"""
import sys
import random
import itertools

import numpy as np
import pandas as pd
import xarray as xr

SEED = 6992
N_FUZZ = 100_000


# --- the R/I shadow: computeNameSets, transliterated from Solution.lean -------

def filter_out(drop, xs):
    """filterOut: order-preserving removal of every name occurring in `drop`."""
    return [x for x in xs if x not in drop]


def compute_name_sets(is_multi, dim, levels, R, V, C, drop_f):
    """Faithful transliteration of `computeNameSets` (Solution.lean pure region).
    Returns (vars, coords, idxs) as lists; the caller compares as sets."""
    Rset = set(R)

    def mk(dv, nv, ni):
        return (filter_out(dv, V) + nv, filter_out(dv, C), ni)

    if is_multi:
        keep_levels = [k for k in levels if k not in Rset]
        if (dim not in Rset) and keep_levels:
            reset_levels = [k for k in levels if k in Rset]
            if len(keep_levels) == 1:
                if drop_f:
                    return mk(keep_levels + reset_levels, [dim], [dim])
                else:
                    return mk(keep_levels, [dim] + reset_levels, [dim])
            else:
                if drop_f:
                    return mk(reset_levels, keep_levels, keep_levels + [dim])
                else:
                    return mk([], keep_levels + reset_levels, keep_levels + [dim])
        else:
            if drop_f:
                return mk([dim] + levels, [], [])
            else:
                return mk([dim], levels, [])
    else:
        if drop_f:
            return mk([dim], [], [])
        else:
            return mk([], [dim], [])


# --- model-input extraction from a real Dataset (the mapping.md bijection) ----

def model_inputs(ds, index_key, R):
    """Derive (is_multi, dim, levels, R, V, C) for the single index group keyed
    by `index_key`.  `levels`/`dim` come from the REAL index object — i.e. the
    A-referenced footprint validated by G-AX."""
    idx = ds._indexes[index_key]
    is_multi = isinstance(idx, xr.core.indexes.PandasMultiIndex)
    dim = idx.dim
    if is_multi:
        levels = [n for n in idx.index.names if n is not None]
    else:
        levels = []
    V = list(ds._variables.keys())
    C = list(ds._coord_names)
    return is_multi, dim, levels, list(R), V, C


# --- the oracle: patched reset_index name-sets --------------------------------

def oracle_name_sets(ds, R, drop):
    arg = R[0] if len(R) == 1 else list(R)
    out = ds.reset_index(arg, drop=drop)            # patched callee (gold applied)
    return (set(out._variables.keys()),
            set(out._coord_names),
            set(out._indexes.keys()))


# --- dataset generators -------------------------------------------------------

def make_single(dim, size):
    return xr.Dataset(coords={dim: list(range(size))})


def make_multi(dim, names, size, extra_vars=False, extra_coord=False):
    arrays = []
    for j, _ in enumerate(names):
        if j == 0:
            arrays.append([chr(ord("a") + (i % 3)) for i in range(size)])
        else:
            arrays.append([(i + j) % 4 for i in range(size)])
    midx = pd.MultiIndex.from_arrays(arrays, names=names)
    coords = {dim: midx}
    data_vars = {}
    if extra_coord:
        coords["scal"] = 99
    if extra_vars:
        data_vars["d"] = (dim, list(range(size)))
    return xr.Dataset(data_vars=data_vars, coords=coords)


def footprint(ds, index_key):
    idx = ds._indexes[index_key]
    fp = {idx.dim}
    if isinstance(idx, xr.core.indexes.PandasMultiIndex):
        fp |= {n for n in idx.index.names if n is not None}
    return sorted(fp)


def cases():
    """Yield (build_fn, index_key, footprint_names, is_multi_flag) factories.
    Each `build_fn()` returns a FRESH dataset (reset_index mutates nothing but we
    want independent objects)."""
    # single index, dim x
    yield (lambda: make_single("x", 3), "x")
    yield (lambda: make_single("t", 5), "t")
    # 2-level multi
    yield (lambda: make_multi("x", ("foo", "bar"), 4), "x")
    # 2-level multi with extra data var + non-index coord
    yield (lambda: make_multi("x", ("foo", "bar"), 4, extra_vars=True, extra_coord=True), "x")
    # 3-level multi
    yield (lambda: make_multi("x", ("a", "b", "c"), 4), "x")
    # 3-level multi, different dim name
    yield (lambda: make_multi("dim0", ("g", "h", "k"), 6), "dim0")


def all_requests(fp):
    """Every non-empty subset of the footprint is a valid reset target."""
    subs = []
    for r in range(1, len(fp) + 1):
        for combo in itertools.combinations(fp, r):
            subs.append(list(combo))
    return subs


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    work = []  # (build_fn, index_key, R, drop)
    # exhaustive: every case × every non-empty footprint subset × both drop flags
    for build_fn, key in cases():
        ds0 = build_fn()
        fp = footprint(ds0, key)
        for R in all_requests(fp):
            for drop in (False, True):
                work.append((build_fn, key, R, drop))

    # then pad with randomized fuzz over the same families to reach N_FUZZ
    case_list = list(cases())
    while len(work) < N_FUZZ:
        build_fn, key = rng.choice(case_list)
        ds0 = build_fn()
        fp = footprint(ds0, key)
        r = rng.randint(1, len(fp))
        R = rng.sample(fp, r)
        drop = rng.choice([False, True])
        work.append((build_fn, key, R, drop))

    for build_fn, key, R, drop in work:
        count += 1
        ds = build_fn()
        is_multi, dim, levels, Rl, V, C = model_inputs(ds, key, R)
        sh_vars, sh_coords, sh_idxs = compute_name_sets(
            is_multi, dim, levels, Rl, V, C, drop)
        shadow = (set(sh_vars), set(sh_coords), set(sh_idxs))
        try:
            oracle = oracle_name_sets(build_fn(), R, drop)
        except Exception as e:  # noqa: BLE001
            disagreements.append((key, R, drop, shadow, "EXC:%r" % e))
            if len(disagreements) >= 5:
                break
            continue
        if shadow != oracle:
            disagreements.append((key, R, drop, shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for key, R, drop, sh, orc in disagreements:
            print("  index=%r reset=%r drop=%r shadow=%r oracle=%r"
                  % (key, R, drop, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of computeNameSets agrees with patch.diff "
          "(patched reset_index) name-sets on %d inputs (seed=%d), 0 "
          "disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
