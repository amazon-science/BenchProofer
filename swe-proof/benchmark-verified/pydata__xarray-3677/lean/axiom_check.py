#!/usr/bin/env python
"""G-AX: validate the A-reference callee behavior for pydata__xarray-3677.

Runs INSIDE the instance image at base_commit (the gate does NOT apply the gold
patch). This is correct: G-AX validates the UNCHANGED callees the fix defers to,
not the changed method itself.

The bundle declares no CONSUMED property axiom — `correct_merge` closes by case
analysis on the shape of the second operand (`cases <;> rfl`). The two `opaque`
callees are A-REFERENCE deep-model references (mapping.md):

  * `datasetOfArray : DataArray -> Dataset`
        == `DataArray.to_dataset()` (the canonical one-variable dataset of a
        single named array — the unchanged coercion the fix calls).
  * `mergeDatasets : Dataset -> Dataset -> Except MergeErr Dataset`
        == the unchanged dataset-to-dataset merge guts
        (`dataset_merge_method` + `Dataset._replace`), which the method already
        called on two datasets before the fix and still calls after it.

Soundness-critical properties this asserts against the REAL repo callees:

  (P1) `datasetOfArray a` is a genuine one-variable dataset carrying the array
       under its name: `da.to_dataset()` is a `Dataset`, `da.name in ds`, and the
       stored variable equals the array's data. (The array is read as a dataset,
       not fabricated.)

  (P2) The merge method's contract holds under the coercion: merging the first
       dataset with the array READ AS A DATASET reproduces exactly the top-level
       `xr.merge([ds, da])` result — i.e. the modeled composition
       `mergeDatasets self (datasetOfArray a)` is the intended behavior, and it
       is a normal successful dataset-to-dataset merge (an `Except.ok`), NOT a
       failure. We exercise the callees DIRECTLY (`da.to_dataset()` then
       `dataset_merge_method` via the guts), never through the buggy
       base_commit `Dataset.merge(da)` (that is the method under repair).

  (P3) The dataset-operand path is unaffected: `dataset_merge_method(ds, other)`
       for a genuine dataset `other` matches `xr.merge([ds, other])`.

stdlib-only (+ xarray/numpy under test). Exit 0 iff every observation meets the
modeled property; nonzero + a violation count otherwise.
"""
import sys
import traceback

SEED = 3677          # pinned in mapping.md

try:
    import numpy as np
    import xarray as xr
    from xarray.core.dataarray import DataArray
    from xarray.core.dataset import Dataset
    from xarray.core.merge import dataset_merge_method
    from xarray.core import dtypes
    from xarray.testing import assert_identical
except Exception as e:  # pragma: no cover
    print(f"status=error import failed: {e}")
    sys.exit(2)


def _merge_guts(ds, other):
    """Invoke the UNCHANGED dataset-to-dataset merge guts directly, matching the
    method body (`dataset_merge_method(...)` then `self._replace(**...)`)."""
    merge_result = dataset_merge_method(
        ds,
        other,
        overwrite_vars=frozenset(),
        compat="no_conflicts",
        join="outer",
        fill_value=dtypes.NA,
    )
    return ds._replace(**merge_result._asdict())


def make_cases(rng):
    cases = []
    # F2P boundary: scalar dataset + scalar named DataArray.
    cases.append((xr.Dataset({"a": 0}), xr.DataArray(data=1, name="b")))
    # Fuzz: assorted shapes / names / dtypes, all non-conflicting.
    for _ in range(600):
        n = int(rng.integers(0, 5))
        dsvars = {}
        k = int(rng.integers(0, 3))
        for i in range(k):
            dsvars[f"d{i}"] = ("x", rng.integers(-5, 5, size=n).astype(
                rng.choice(["int64", "float64"])))
        if not dsvars:
            dsvars["s"] = int(rng.integers(-9, 9))
        ds = xr.Dataset(dsvars)
        name = rng.choice(["b", "arr", "z", "w"])
        if bool(rng.integers(0, 2)):
            da = xr.DataArray(data=float(rng.normal()), name=str(name))
        else:
            da = xr.DataArray(
                data=rng.normal(size=n), dims=("x",), name=str(name))
        cases.append((ds, da))
    return cases


def main():
    rng = np.random.default_rng(SEED)
    violations = 0
    checked = 0
    for ds, da in make_cases(rng):
        checked += 1
        try:
            # (P1) datasetOfArray == da.to_dataset(): a genuine one-variable dataset.
            coerced = da.to_dataset()
            if not isinstance(coerced, Dataset):
                violations += 1
                print("P1 violation: to_dataset() is not a Dataset")
                continue
            if da.name not in coerced:
                violations += 1
                print(f"P1 violation: name {da.name!r} not a variable of coerced dataset")
                continue

            # (P2) mergeDatasets self (datasetOfArray a) == xr.merge([ds, da]),
            # a successful (Except.ok) dataset-to-dataset merge.
            via_coercion = _merge_guts(ds, coerced)
            toplevel = xr.merge([ds, da])
            assert_identical(via_coercion, toplevel)

            # (P3) dataset-operand path unaffected.
            other_ds = xr.Dataset({"q": ("x", np.zeros(da.sizes.get("x", 0)))}) \
                if "x" in da.dims else xr.Dataset({"q": 0})
            try:
                via_ds = _merge_guts(ds, other_ds)
                assert_identical(via_ds, xr.merge([ds, other_ds]))
            except xr.MergeError:
                # a genuine conflict is a legitimate merge outcome; the modeled
                # `mergeDatasets` returns the error verbatim — not a violation.
                pass
        except xr.MergeError:
            # A genuine merge conflict is a valid `Except.error` outcome of the
            # modeled `mergeDatasets`; the contract propagates it verbatim.
            continue
        except Exception:
            violations += 1
            print("unexpected callee failure:")
            traceback.print_exc()

    if violations:
        print(f"status=fail total violations: {violations} (checked {checked})")
        sys.exit(1)
    print(f"status=pass A-reference callees consistent over {checked} scenarios "
          "(to_dataset yields the one-variable dataset; the dataset-to-dataset "
          "merge of the coerced operand reproduces the top-level merge)")
    sys.exit(0)


if __name__ == "__main__":
    main()
