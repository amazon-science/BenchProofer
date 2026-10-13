#!/usr/bin/env python3
"""G-AX executable soundness check for pydata__xarray-3677.

Validates the ONE deep-model reference of this bundle (there are no consumed
axioms) against the REAL unchanged callee it models:

  (A-reference) `combineCore` (Solution.lean pure region) == the unchanged core
      combine machinery `xarray.core.merge.dataset_merge_method` (-> merge_core
      -> coerce_pandas_values), the operation the patched operand-handling tail
      feeds:

        combineCore base (.keyed es) = .ok (base ++ es)
            <=>  dataset_merge_method(self, mapping_operand) yields the union of
                 the two variable mappings (disjoint-name regime)
        combineCore base (.single _ _) = .error .notKeyed
            <=>  dataset_merge_method(self, raw_DataArray) raises AttributeError
                 ('DataArray' object has no attribute 'items')

The second observation is the crash the issue reports and the reason the fix
re-expresses a raw DataArray operand into a Dataset before the combine.

Imports `xarray` — the same package the gold patch lives in (the repo under
test); plus stdlib. Exit 0 iff every obligation holds.
"""
import random
import sys

import xarray as xr
from xarray.core.merge import dataset_merge_method


def _entries(ds):
    """Observable projection of a Dataset: the {name: scalar value} mapping the
    F2P test's `assert_identical` distinguishes (for scalar int variables)."""
    return {str(k): int(v.values) for k, v in ds.data_vars.items()}


def check_keyed_reference(base_map, other_map):
    """A-reference, keyed case: combineCore base (.keyed es) = .ok (base ++ es)
    <=> real dataset_merge_method on a Dataset operand yields the union (the
    disjoint-name regime)."""
    base = xr.Dataset({k: v for k, v in base_map.items()})
    other = xr.Dataset({k: v for k, v in other_map.items()})
    res = dataset_merge_method(                       # real callee
        base, other,
        overwrite_vars=frozenset(), compat="no_conflicts",
        join="outer", fill_value=xr.core.dtypes.NA,
    )
    merged = base._replace(**res._asdict())
    expected = dict(base_map)
    expected.update(other_map)
    got = _entries(merged)
    assert got == {str(k): int(v) for k, v in expected.items()}, (
        "combineCore deep model unsound (keyed case): merge of %r and %r gave "
        "%r, model requires the union %r" % (base_map, other_map, got, expected))


def check_single_reference(base_map, name, value):
    """A-reference, single case: combineCore base (.single _ _) = .error
    .notKeyed <=> real dataset_merge_method on a raw DataArray raises
    AttributeError (the reported crash)."""
    base = xr.Dataset({k: v for k, v in base_map.items()})
    da = xr.DataArray(data=value, name=name)
    raised = False
    try:
        dataset_merge_method(                         # real callee, RAW DataArray
            base, da,
            overwrite_vars=frozenset(), compat="no_conflicts",
            join="outer", fill_value=xr.core.dtypes.NA,
        )
    except AttributeError:
        raised = True
    assert raised, (
        "combineCore deep model unsound (single case): "
        "dataset_merge_method on a raw DataArray %r did not raise AttributeError; "
        "model requires .error .notKeyed" % (name,))


def main():
    rng = random.Random(3677)
    names = ["a", "b", "c", "d", "e", "x", "y", "z"]

    # --- A-reference, keyed case: boundary + fuzz (disjoint-name regime) ----
    boundary = [
        ({"a": 0}, {"b": 1}),                          # the F2P scenario
        ({}, {"b": 1}),
        ({"a": 0}, {}),
        ({"a": 0, "c": 5}, {"b": 1, "d": 2}),
    ]
    for base_map, other_map in boundary:
        check_keyed_reference(base_map, other_map)

    for _ in range(2000):
        n = rng.randint(0, 4)
        m = rng.randint(0, 4)
        keys = rng.sample(names, min(n + m, len(names)))
        bkeys, okeys = keys[:n], keys[n:n + m]
        base_map = {k: rng.randint(-1000, 1000) for k in bkeys}
        other_map = {k: rng.randint(-1000, 1000) for k in okeys}
        check_keyed_reference(base_map, other_map)

    # --- A-reference, single case: the reported crash ----------------------
    n_crash = 0
    for name in names:
        for base_map in ({"a": 0}, {}, {"a": 0, "c": 5}):
            check_single_reference(base_map, name, rng.randint(-1000, 1000))
            n_crash += 1

    print("G-AX OK: combineCore deep model (== dataset_merge_method) sound on "
          "%d boundary + 2000 fuzz mapping merges and %d raw-DataArray crash "
          "checks" % (len(boundary), n_crash))
    return 0


if __name__ == "__main__":
    sys.exit(main())
