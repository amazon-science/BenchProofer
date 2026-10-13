#!/usr/bin/env python3
r"""G-CONF differential conformance check for pydata__xarray-4695 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour:
the real `xarray.core.dataarray._LocIndexer.__getitem__` (i.e. `DataArray.loc[key]`).

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled `labelSelect`: the result of label-based
              selection is determined by the applied (dimension, labels) mapping,
              with EVERY entry of the mapping honoured as a dimension/label
              request, in order, regardless of the textual dimension names
              (`out = Except.ok key`). Transliterated to Python over the real
              repo types via the mapping.md §2 bijection:
                  key : List (String × Label)  <->  the dict passed to da.loc[...]
                  String                        <->  a dimension name
                  Label = List String           <->  the list of tick labels
                                                      requested along that dim
              The shadow computes the selected sub-array DIRECTLY from the
              coordinate label tables (positional indexing of the underlying
              numpy buffer by the integer positions of the requested labels in
              each dimension's coordinate list) — it never calls `.sel`/`.loc`,
              so it is an independent oracle for "all entries applied".
              There are NO A-tagged ops (no consumed axioms, no deep-model
              references), so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched `DataArray.loc[key]`
              (the patched `_LocIndexer.__getitem__`, which now calls
              `self.data_array.sel(key)` positionally).

They must agree (same selected values, same result shape, same coordinate
labels along each axis) on every input, INCLUDING mappings whose dimension names
collide with `sel`'s own option names ("method", "tolerance", "drop",
"indexers"). Exit 0 iff zero disagreements; any disagreement is a mechanical
R/I-fidelity counterexample.

stdlib + numpy + xarray only. No I/O, no DB. Fuzz seed pinned (mapping.md §4).
"""
import sys
import random
import itertools

SEED = 4695
N_FUZZ = 100_000

# Dimension-name pool: a mix of ordinary names and names that collide with
# DataArray.sel's reserved parameters (the discriminating cases the issue
# reports). All four reserved names appear so the fuzzer exercises every
# collision, not only "method".
RESERVED = ["method", "tolerance", "drop", "indexers"]
ORDINARY = ["dim1", "dim2", "x", "y", "time", "lat", "lon"]
NAME_POOL = RESERVED + ORDINARY

# Coordinate-label alphabet (distinct string labels per dimension).
LABELS = ["a", "b", "c", "d", "e", "f", "g", "h"]


def _shadow_select(values, dims, coords, key):
    """Independent oracle for Solution.lean's `labelSelect` over the real types.

    Selects along EVERY dimension named in `key` using the requested label
    lists, by positional indexing of the numpy buffer `values` — never touching
    xarray's `.sel`/`.loc`. Returns (selected_ndarray, result_dims,
    result_coords) describing the array the model says `.loc[key]` must yield.
    Honours all entries regardless of name (the spec: out = Except.ok key)."""
    import numpy as np

    idx = []
    res_dims = []
    res_coords = {}
    for axis, d in enumerate(dims):
        clist = coords[d]
        if d in key:
            wanted = key[d]
            positions = [clist.index(lbl) for lbl in wanted]
            idx.append(positions)
            res_dims.append(d)
            res_coords[d] = [clist[p] for p in positions]
        else:
            idx.append(list(range(len(clist))))
            res_dims.append(d)
            res_coords[d] = list(clist)
    # Orthogonal (outer) indexing, matching xarray label selection with list
    # indexers: np.ix_ builds the open mesh so each axis is indexed independently.
    selected = values[np.ix_(*idx)]
    return selected, res_dims, res_coords


def _oracle_loc(values, dims, coords, key):
    """The REAL patched behaviour: build the DataArray and apply `.loc[key]`."""
    import numpy as np
    import xarray as xr

    da = xr.DataArray(values, dims=dims, coords={d: coords[d] for d in dims})
    return da.loc[key]


def _gen_case(rng):
    """Generate one fuzzed (values, dims, coords, key)."""
    ndim = rng.randint(1, 3)
    # distinct dimension names, biased to include reserved names often
    names = rng.sample(NAME_POOL, ndim)
    if rng.random() < 0.6:
        # force at least one reserved name into the dims to stress the collision
        pos = rng.randrange(ndim)
        names[pos] = rng.choice(RESERVED)
        # keep names distinct
        seen = set()
        for i, nm in enumerate(names):
            while nm in seen:
                nm = rng.choice(NAME_POOL)
            names[i] = nm
            seen.add(nm)
    dims = names
    coords = {}
    shape = []
    for d in dims:
        size = rng.randint(1, len(LABELS))
        labels = rng.sample(LABELS, size)
        coords[d] = labels
        shape.append(size)
    import numpy as np
    rs = np.random.RandomState(rng.randrange(2**31))
    values = rs.randint(-1000, 1000, size=tuple(shape)).astype("int64")

    # Build the indexer dict: select a subset of dims (possibly all/none-but-one),
    # each with a non-empty subset of its labels (list-valued -> keeps the dim).
    chosen = [d for d in dims if rng.random() < 0.75]
    if not chosen:
        chosen = [rng.choice(dims)]
    key = {}
    for d in chosen:
        clist = coords[d]
        k = rng.randint(1, len(clist))
        # ordered subset of labels (preserve a requested order)
        picks = rng.sample(clist, k)
        key[d] = picks
    return values, dims, coords, key


def main():
    try:
        import numpy as np
        import xarray as xr  # noqa: F401
    except Exception as e:  # pragma: no cover
        print(f"G-CONF ERROR: imports unavailable in container: {e!r}")
        return 2

    rng = random.Random(SEED)
    disagreements = 0
    first = None
    checked = 0

    for n in range(N_FUZZ):
        values, dims, coords, key = _gen_case(rng)
        try:
            sel_vals, res_dims, res_coords = _shadow_select(values, dims, coords, key)
        except Exception as e:  # pragma: no cover
            print(f"G-CONF ERROR: shadow raised on case {n}: {e!r}")
            return 2
        try:
            got = _oracle_loc(values, dims, coords, key)
        except Exception as e:
            disagreements += 1
            if first is None:
                first = (dims, coords, key, f"oracle .loc raised: {e!r}")
            continue

        checked += 1
        ok = True
        # 1) result dimension order
        if list(got.dims) != list(res_dims):
            ok = False
        # 2) per-dimension coordinate labels (which labels, in which order)
        if ok:
            for d in res_dims:
                got_coord = [str(v) for v in got.coords[d].values.tolist()]
                exp_coord = [str(v) for v in res_coords[d]]
                if got_coord != exp_coord:
                    ok = False
                    break
        # 3) selected values
        if ok:
            if not np.array_equal(np.asarray(got.values), np.asarray(sel_vals)):
                ok = False

        if not ok:
            disagreements += 1
            if first is None:
                first = (dims, coords, key,
                         f"got dims={list(got.dims)} vals={np.asarray(got.values).tolist()} "
                         f"expected dims={res_dims} vals={np.asarray(sel_vals).tolist()}")

    if disagreements:
        print(f"G-CONF FAIL: {disagreements}/{N_FUZZ} disagreements (seed={SEED}). "
              f"First: {first}")
        return 1

    print(f"G-CONF OK: R/I shadow of labelSelect agrees with patch.diff behaviour "
          f"on {checked} inputs (seed={SEED}), 0 disagreements. "
          f"Reserved-named dims (method/tolerance/drop/indexers) exercised.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
